import torch

print("cuda available:", torch.cuda.is_available())
print("torch version:", torch.__version__)
print("torch.cuda version:", torch.version.cuda)
if torch.cuda.is_available():
    print("device count:", torch.cuda.device_count())
    print("device 0:", torch.cuda.get_device_name(0))
