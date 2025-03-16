import argparse
import os
from huggingface_hub import snapshot_download

if __name__ == "__main__": 
    des="""
    Downloads a Hugging Face Model to Local 
    Directory (non-GGUF)
    """

    parser = argparse.ArgumentParser(description=des.lstrip(" "), formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--model", type=str, help="Hugging Face Model\t ['unsloth/Llama-3.2-1B']")
    parser.add_argument("out_dir", type=str, help="Dir to Save Model\t ['./model']")
    args = parser.parse_args()

    if args.model is not None:
        HUGGING_FACE_MODEL = args.model
    else: raise IOError
    if args.out_dir is not None:
        DIR_TO_SAVE = os.path.join(os.getcwd(), args.out_dir)
    else: DIR_TO_SAVE = os.path.join(os.getcwd(), "Llama1B")

    snapshot_download(
        repo_id = HUGGING_FACE_MODEL,
        local_dir = DIR_TO_SAVE
    )
