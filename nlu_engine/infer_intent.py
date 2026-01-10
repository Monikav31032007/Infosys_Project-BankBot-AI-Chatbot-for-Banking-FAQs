# infer_intent.py

import os
import json
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification


class IntentClassifier:
    def __init__(self, model_dir="models/intent_model"):
        self.model_dir = model_dir

        self.label_map = None
        id2label_path = os.path.join(model_dir, "id2label.json")
        label2id_path = os.path.join(model_dir, "label2id.json")
        labels_path = os.path.join(model_dir, "labels.json")

        if os.path.exists(id2label_path):
            with open(id2label_path, "r", encoding="utf-8") as f:
                raw = json.load(f)
            # ensure keys are strings matching model output indices
            self.label_map = {str(int(k)): v for k, v in raw.items()}
        elif os.path.exists(label2id_path):
            with open(label2id_path, "r", encoding="utf-8") as f:
                raw = json.load(f)
            self.label_map = {str(v): k for k, v in raw.items()}
        elif os.path.exists(labels_path):
            with open(labels_path, "r", encoding="utf-8") as f:
                self.label_map = json.load(f)
        else:
            # fallback to id2label in model config
            model_config_path = os.path.join(model_dir, "config.json")
            if os.path.exists(model_config_path):
                from transformers import AutoConfig
                config = AutoConfig.from_pretrained(model_dir)
                # config.id2label is usually a dict mapping ints->str
                self.label_map = {str(int(k)): v for k, v in config.id2label.items()}
            else:
                raise FileNotFoundError("No label map found in model directory (id2label.json, label2id.json or labels.json).")

        # Load tokenizer + model
        self.tokenizer = AutoTokenizer.from_pretrained(model_dir)
        try:
            self.model = AutoModelForSequenceClassification.from_pretrained(model_dir)
        except Exception as e:
            msg = str(e)
            if "meta tensor" in msg or "Cannot copy out of meta tensor" in msg or "no data" in msg.lower():
                raise RuntimeError(
                    f"Model at '{model_dir}' appears to be missing weights or contains placeholder/meta tensors.\n"
                    "Make sure the directory contains the trained weights (e.g. 'pytorch_model.bin' or 'model.safetensors').\n"
                    "If you intended to use a pretrained model from the Hub, provide the model name or download the weights first.\n"
                    f"Original error: {e}"
                ) from e
            raise

        try:
            any_meta = any(p.is_meta for p in self.model.parameters())
        except Exception:
            any_meta = False
        if any_meta:
            raise RuntimeError(
                f"Model at '{model_dir}' contains meta tensors (no parameter data).\n"
                "This usually means the model weights were not saved or were not downloaded.\n"
                "Please retrain the model or place the correct weight files in the model directory."
            )

        self.model.eval()

    def predict(self, text, top_k=1):
        """
        Return top_k predicted intents for a given text
        """
        try:
            inputs = self.tokenizer(text, return_tensors="pt", truncation=True, padding=True)
        except Exception:
            inputs = self.tokenizer(str(text), return_tensors="pt", truncation=True, padding=True)

        with torch.no_grad():
            outputs = self.model(**inputs)

        probs = torch.softmax(outputs.logits, dim=1)[0]
        top_indices = torch.topk(probs, top_k).indices.tolist()

        results = []
        for idx in top_indices:
            key = str(int(idx))
            intent_name = self.label_map.get(key, key)
            confidence = float(probs[idx])
            results.append({"intent": intent_name, "confidence": confidence})

        return results


# Example usage
if __name__ == "__main__":
    try:
        ic = IntentClassifier()
        predictions = ic.predict(
            "Please transfer 5000 to my savings account",
            top_k=3
        )
        for i, p in enumerate(predictions, 1):
            print(f"{i}. Intent: {p['intent']}, Confidence: {p['confidence']:.4f}")
    except Exception as e:
        print("Error:", e)