"""
Chart Pattern Recognition Model Training
Creates a CNN model to classify chart patterns as bullish/bearish
"""
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms, models
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import os
import random

# Pattern types
PATTERNS = {
    # Bullish patterns (0-5)
    0: ("bull_flag", "Bullish Flag", "bullish"),
    1: ("ascending_triangle", "Ascending Triangle", "bullish"),
    2: ("double_bottom", "Double Bottom", "bullish"),
    3: ("inverse_head_shoulders", "Inverse Head & Shoulders", "bullish"),
    4: ("cup_handle", "Cup and Handle", "bullish"),
    5: ("bullish_engulfing", "Bullish Engulfing", "bullish"),
    # Bearish patterns (6-11)
    6: ("bear_flag", "Bearish Flag", "bearish"),
    7: ("descending_triangle", "Descending Triangle", "bearish"),
    8: ("double_top", "Double Top", "bearish"),
    9: ("head_shoulders", "Head & Shoulders", "bearish"),
    10: ("rising_wedge", "Rising Wedge", "bearish"),
    11: ("bearish_engulfing", "Bearish Engulfing", "bearish"),
}

def generate_synthetic_chart(pattern_id, size=(224, 224)):
    """Generate a synthetic chart image for a given pattern"""
    img = Image.new('RGB', size, color=(10, 10, 20))
    draw = ImageDraw.Draw(img)
    
    w, h = size
    margin = 20
    
    # Draw grid
    for i in range(5):
        y = margin + i * (h - 2*margin) // 4
        draw.line([(margin, y), (w-margin, y)], fill=(30, 30, 40), width=1)
    
    pattern_name = PATTERNS[pattern_id][0]
    
    # Generate price points based on pattern
    points = []
    num_points = 50
    
    if pattern_name == "bull_flag":
        # Strong up move, then slight down channel, then up
        for i in range(num_points):
            if i < 15:
                y = h - margin - (i * 8) + random.randint(-3, 3)
            elif i < 35:
                y = h - margin - 120 + ((i-15) * 2) + random.randint(-5, 5)
            else:
                y = h - margin - 80 - ((i-35) * 6) + random.randint(-3, 3)
            x = margin + i * (w - 2*margin) // num_points
            points.append((x, max(margin, min(h-margin, y))))
    
    elif pattern_name == "ascending_triangle":
        resistance = h // 3
        for i in range(num_points):
            cycle = (i % 10) / 10
            base = h - margin - (i * 2)
            if cycle < 0.5:
                y = base - int(cycle * 100)
            else:
                y = resistance + random.randint(-5, 5)
            x = margin + i * (w - 2*margin) // num_points
            points.append((x, max(margin, min(h-margin, y))))
    
    elif pattern_name == "double_bottom":
        for i in range(num_points):
            if i < 12:
                y = margin + 50 + i * 5
            elif i < 20:
                y = h - margin - 30 + random.randint(-10, 10)
            elif i < 30:
                y = h - margin - 30 - (i-20) * 8
            elif i < 38:
                y = h - margin - 30 + random.randint(-10, 10)
            else:
                y = h - margin - 30 - (i-38) * 10
            x = margin + i * (w - 2*margin) // num_points
            points.append((x, max(margin, min(h-margin, y))))
    
    elif pattern_name == "inverse_head_shoulders":
        for i in range(num_points):
            if i < 10:
                y = margin + 40 + i * 6
            elif i < 15:
                y = h - margin - 60 - (i-10) * 8
            elif i < 25:
                y = margin + 30 + abs(i-20) * 12
            elif i < 30:
                y = h - margin - 60 - (i-25) * 8
            elif i < 40:
                y = margin + 40 + (i-30) * 6
            else:
                y = margin + 100 - (i-40) * 8
            x = margin + i * (w - 2*margin) // num_points
            points.append((x, max(margin, min(h-margin, y))))
    
    elif pattern_name == "cup_handle":
        for i in range(num_points):
            if i < 25:
                # Cup part - U shape
                y = margin + 40 + int(80 * (1 - ((i-12.5)/12.5)**2))
            elif i < 35:
                # Handle - small dip
                y = margin + 50 + (i-25) * 3
            else:
                # Breakout
                y = margin + 80 - (i-35) * 5
            x = margin + i * (w - 2*margin) // num_points
            points.append((x, max(margin, min(h-margin, y))))
    
    elif pattern_name == "bullish_engulfing":
        for i in range(num_points):
            if i < 40:
                y = margin + 40 + i * 3 + random.randint(-5, 5)
            else:
                y = h - margin - 40 - (i-40) * 8
            x = margin + i * (w - 2*margin) // num_points
            points.append((x, max(margin, min(h-margin, y))))
    
    elif pattern_name == "bear_flag":
        for i in range(num_points):
            if i < 15:
                y = margin + 40 + i * 8 + random.randint(-3, 3)
            elif i < 35:
                y = h - margin - 60 - ((i-15) * 2) + random.randint(-5, 5)
            else:
                y = margin + 80 + (i-35) * 6 + random.randint(-3, 3)
            x = margin + i * (w - 2*margin) // num_points
            points.append((x, max(margin, min(h-margin, y))))
    
    elif pattern_name == "descending_triangle":
        support = h - h // 3
        for i in range(num_points):
            cycle = (i % 10) / 10
            top = margin + 40 + (i * 2)
            if cycle < 0.5:
                y = top + int(cycle * 80)
            else:
                y = support + random.randint(-5, 5)
            x = margin + i * (w - 2*margin) // num_points
            points.append((x, max(margin, min(h-margin, y))))
    
    elif pattern_name == "double_top":
        for i in range(num_points):
            if i < 12:
                y = h - margin - 50 - i * 5
            elif i < 20:
                y = margin + 30 + random.randint(-10, 10)
            elif i < 30:
                y = margin + 30 + (i-20) * 8
            elif i < 38:
                y = margin + 30 + random.randint(-10, 10)
            else:
                y = margin + 30 + (i-38) * 10
            x = margin + i * (w - 2*margin) // num_points
            points.append((x, max(margin, min(h-margin, y))))
    
    elif pattern_name == "head_shoulders":
        for i in range(num_points):
            if i < 10:
                y = h - margin - 40 - i * 6
            elif i < 15:
                y = margin + 60 + (i-10) * 8
            elif i < 25:
                y = h - margin - 30 - abs(i-20) * 12
            elif i < 30:
                y = margin + 60 + (i-25) * 8
            elif i < 40:
                y = h - margin - 40 - (i-30) * 6
            else:
                y = h - margin - 100 + (i-40) * 8
            x = margin + i * (w - 2*margin) // num_points
            points.append((x, max(margin, min(h-margin, y))))
    
    elif pattern_name == "rising_wedge":
        for i in range(num_points):
            cycle = (i % 8) / 8
            lower = h - margin - 40 - i * 2
            upper = margin + 60 + i * 1
            if cycle < 0.5:
                y = lower + int(cycle * (lower - upper) * 0.8)
            else:
                y = upper + int((1-cycle) * (lower - upper) * 0.2)
            if i > 40:
                y = y + (i-40) * 5
            x = margin + i * (w - 2*margin) // num_points
            points.append((x, max(margin, min(h-margin, y))))
    
    elif pattern_name == "bearish_engulfing":
        for i in range(num_points):
            if i < 40:
                y = h - margin - 40 - i * 3 + random.randint(-5, 5)
            else:
                y = margin + 40 + (i-40) * 8
            x = margin + i * (w - 2*margin) // num_points
            points.append((x, max(margin, min(h-margin, y))))
    
    # Draw the price line
    if len(points) > 1:
        # Add some noise
        noisy_points = [(p[0], p[1] + random.randint(-2, 2)) for p in points]
        
        # Draw with gradient color
        for i in range(len(noisy_points) - 1):
            color = (100, 200, 100) if PATTERNS[pattern_id][2] == "bullish" else (200, 100, 100)
            draw.line([noisy_points[i], noisy_points[i+1]], fill=color, width=2)
    
    # Add some candlestick-like elements
    for i in range(0, len(points), 5):
        if i < len(points):
            x, y = points[i]
            height = random.randint(5, 15)
            is_green = random.random() > 0.5
            color = (50, 180, 80) if is_green else (180, 50, 50)
            draw.rectangle([x-2, y-height, x+2, y+height], fill=color)
    
    return img


class SyntheticChartDataset(Dataset):
    """Dataset that generates synthetic chart patterns on the fly"""
    
    def __init__(self, num_samples=10000, transform=None):
        self.num_samples = num_samples
        self.transform = transform
        self.num_patterns = len(PATTERNS)
    
    def __len__(self):
        return self.num_samples
    
    def __getitem__(self, idx):
        pattern_id = idx % self.num_patterns
        img = generate_synthetic_chart(pattern_id)
        
        if self.transform:
            img = self.transform(img)
        
        return img, pattern_id


class ChartPatternCNN(nn.Module):
    """CNN for chart pattern classification"""
    
    def __init__(self, num_classes=12):
        super().__init__()
        # Use pretrained ResNet18 as backbone
        self.backbone = models.resnet18(weights=None)
        self.backbone.fc = nn.Linear(512, num_classes)
    
    def forward(self, x):
        return self.backbone(x)


def train_model(epochs=10, batch_size=32, lr=0.001, save_path="chart_classifier.pt"):
    """Train the chart pattern classifier"""
    
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Training on {device}")
    
    # Transforms
    transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.RandomHorizontalFlip(p=0.3),
        transforms.RandomRotation(5),
        transforms.ColorJitter(brightness=0.2, contrast=0.2),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])
    
    # Dataset
    train_dataset = SyntheticChartDataset(num_samples=12000, transform=transform)
    val_dataset = SyntheticChartDataset(num_samples=2400, transform=transform)
    
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True, num_workers=0)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False, num_workers=0)
    
    # Model
    model = ChartPatternCNN(num_classes=12).to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=lr)
    scheduler = optim.lr_scheduler.StepLR(optimizer, step_size=3, gamma=0.5)
    
    best_acc = 0
    
    for epoch in range(epochs):
        # Training
        model.train()
        train_loss = 0
        train_correct = 0
        train_total = 0
        
        for batch_idx, (images, labels) in enumerate(train_loader):
            images, labels = images.to(device), labels.to(device)
            
            optimizer.zero_grad()
            outputs = model(images)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()
            
            train_loss += loss.item()
            _, predicted = outputs.max(1)
            train_total += labels.size(0)
            train_correct += predicted.eq(labels).sum().item()
            
            if batch_idx % 50 == 0:
                print(f"Epoch {epoch+1}/{epochs} | Batch {batch_idx}/{len(train_loader)} | Loss: {loss.item():.4f}")
        
        train_acc = 100. * train_correct / train_total
        
        # Validation
        model.eval()
        val_correct = 0
        val_total = 0
        
        with torch.no_grad():
            for images, labels in val_loader:
                images, labels = images.to(device), labels.to(device)
                outputs = model(images)
                _, predicted = outputs.max(1)
                val_total += labels.size(0)
                val_correct += predicted.eq(labels).sum().item()
        
        val_acc = 100. * val_correct / val_total
        
        print(f"Epoch {epoch+1}/{epochs} | Train Acc: {train_acc:.2f}% | Val Acc: {val_acc:.2f}%")
        
        # Save best model
        if val_acc > best_acc:
            best_acc = val_acc
            # Save as TorchScript for deployment
            model.eval()
            example_input = torch.randn(1, 3, 224, 224).to(device)
            traced = torch.jit.trace(model, example_input)
            traced.save(save_path)
            print(f"Saved best model with {val_acc:.2f}% accuracy")
        
        scheduler.step()
    
    print(f"\nTraining complete! Best accuracy: {best_acc:.2f}%")
    return save_path


if __name__ == "__main__":
    import sys
    epochs = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    save_path = sys.argv[2] if len(sys.argv) > 2 else "chart_classifier.pt"
    train_model(epochs=epochs, save_path=save_path)
