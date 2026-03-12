import os
from pathlib import Path
import json

import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torchvision import datasets, models, transforms


# ----- Configurations -----
DATA_DIR = Path("data")  # Directory containing 'train' and 'val' subdirectories
BATCH_SIZE = 16
NUM_EPOCHS = 15
LEARNING_RATE = 1e-4
MODEL_OUT = "lettuce_model.pth"


def main():
    #Transformations for training and validation datasets
    imagenet_mean = [0.485, 0.456, 0.406]
    imagenet_std  = [0.229, 0.224, 0.225]

    train_tf = transforms.Compose([
        #resize for standard mobilenet input
        transforms.Resize((224, 224)),
        #flip images since plants can be in any orientation
        transforms.RandomHorizontalFlip(),
        #rotate slightly since leaves can be at different angles
        transforms.RandomRotation(10),
        #lighting variations so model knows it's not just potassium deficiency
        transforms.ColorJitter(brightness=0.2, contrast=0.2),
        #adds blur since webcam can be low quality to prevent mistaking for nitrogen deficiency
        transforms.GaussianBlur(kernel_size=5, sigma=(0.1, 2.0)),
        #add sharpness variations since camera quality is not good
        transforms.RandomAdjustSharpness(sharpness_factor=0.5, p=0.5),
        #convert from images to matrix form
        transforms.ToTensor(),
        transforms.Normalize(imagenet_mean, imagenet_std)
    ])

    val_tf = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(imagenet_mean, imagenet_std),
    ])

    # directory to datasets
    train_dir = DATA_DIR / "train"
    val_dir = DATA_DIR / "val"

    train_ds = datasets.ImageFolder(str(train_dir), transform=train_tf)
    val_ds = datasets.ImageFolder(str(val_dir), transform=val_tf)

    train_loader = DataLoader(train_ds, batch_size=BATCH_SIZE, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=BATCH_SIZE, shuffle=False)

    print("Class to index mapping:", train_ds.class_to_idx)

    # ----- Model -----
    # Use GPU if available
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print("Using device:", device)

    #using MobileNetV2 pretrained on ImageNet for raspberri pi efficiency
    model = models.mobilenet_v2(weights=models.MobileNet_V2_Weights.IMAGENET1K_V1)

    # Replace final classifier layer: 1000 -> 4 classes
    model.classifier[1] = nn.Linear(model.last_channel, 4)

    #ensure model is on the correct gpu/cpu
    model = model.to(device)

    #reduce loss and increase efficiency with Adam optimizer
    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=LEARNING_RATE)

    # ----- Training loop
    for epoch in range(NUM_EPOCHS):
        model.train()
        running_loss = 0.0

        #loop through images and labels in training data
        for images, labels in train_loader:
            #move to gpu/cpu
            images, labels = images.to(device), labels.to(device)
            
            #erase previous mistakes
            optimizer.zero_grad()

            #make predictions
            outputs = model(images)

            #compare predictions to actual labels
            loss = criterion(outputs, labels)

            #fix errors
            loss.backward()
            optimizer.step()

            #track loss
            running_loss += loss.item() * images.size(0)

        epoch_loss = running_loss / len(train_ds)

        # ----- Validation -----
        model.eval()
        correct = 0
        total = 0
        val_loss = 0.0

        #without changing model parameters
        with torch.no_grad():
            #loop through images and labels in validation data
            for images, labels in val_loader:
                #move to gpu/cpu
                images, labels = images.to(device), labels.to(device)
                #output 2 class predictions needs_water or ok
                outputs = model(images)
                #check for incorrect predictions
                loss = criterion(outputs, labels)
                val_loss += loss.item() * images.size(0)
                
                #using class with highest score as prediction
                _, preds = torch.max(outputs, 1)
                correct += (preds == labels).sum().item()
                total += labels.size(0)

        val_loss /= len(val_ds)
        val_acc = correct / total if total > 0 else 0.0

        print(f"Epoch {epoch+1}/{NUM_EPOCHS} "
              f"- train_loss: {epoch_loss:.4f} "
              f"- val_loss: {val_loss:.4f} "
              f"- val_acc: {val_acc*100:.1f}%")

    # ----- Save model -----
    torch.save(model.state_dict(), MODEL_OUT)
    print(f"Saved model to {MODEL_OUT}")


if __name__ == "__main__":
    main()