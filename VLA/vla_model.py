# Gian Fernandez 10/23/26
# Load the existing SmolVLM action model and make a prediction from a frame.
# Used AI-assistance 

from pathlib import Path
from time import perf_counter

import torch
from peft import PeftModel
from transformers import AutoProcessor, Idefics3ForConditionalGeneration

BASE_MODEL = "HuggingFaceTB/SmolVLM-Base"
ADAPTER = Path.home() / "offline-robotcs" / "smolvlm_turtlebot_action_balanced"


class Predictor:
    def __init__(self):
        if not torch.cuda.is_available():
            raise RuntimeError("CUDA is not available")

        self.processor = AutoProcessor.from_pretrained(str(ADAPTER))
        base = Idefics3ForConditionalGeneration.from_pretrained(
            BASE_MODEL, dtype=torch.float16
        ).to("cuda")
        self.model = PeftModel.from_pretrained(base, str(ADAPTER)).eval()

    @torch.inference_mode()
    def predict(self, image, instruction=""):
        # The model was trained to return one robot_action, not a whole plan.
        prompt = (
            f"Task: {instruction}\n" if instruction else ""
        ) + "Frame captured by TurtleBot. Respond with only the exact robot_action value."

        messages = [{
            "role": "user",
            "content": [{"type": "image"}, {"type": "text", "text": prompt}],
        }]
        text = self.processor.apply_chat_template(
            messages, add_generation_prompt=True, tokenize=False
        )
        inputs = self.processor(text=[text], images=[image.convert("RGB")], return_tensors="pt")
        inputs = {
            key: value.to("cuda", dtype=torch.float16) if value.is_floating_point() else value.to("cuda")
            for key, value in inputs.items()
        }

        start = perf_counter()
        output = self.model.generate(**inputs, max_new_tokens=24, do_sample=False)
        torch.cuda.synchronize()
        print(f"Inference: {perf_counter() - start:.2f}s", flush=True)

        answer = output[:, inputs["input_ids"].shape[1]:]
        return self.processor.batch_decode(answer, skip_special_tokens=True)[0].strip()


if __name__ == "__main__":
    # Keep the original standalone image test available.
    import sys
    from PIL import Image

    if len(sys.argv) != 2:
        raise SystemExit("Usage: python vla_model.py <image_path>")
    with Image.open(sys.argv[1]) as picture:
        print("Predicted action:", Predictor().predict(picture))
