import os
import cv2
import albumentations as A

def load_obb_labels(label_file):
    """
    Load OBB labels from the format:
    class_id x1 y1 x2 y2 x3 y3 x4 y4 (normalized)
    """
    boxes = []
    with open(label_file, 'r') as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) != 9:  # class_id + 4 corners (x, y)
                continue
            class_id = int(parts[0])
            # Parse the 4 corners (normalized coordinates)
            points = [(float(parts[i]), float(parts[i+1])) for i in range(1, 9, 2)]
            boxes.append([class_id, points])
    return boxes

def save_obb_labels(label_file, boxes):
    """
    Save OBB labels back to the format:
    class_id x1 y1 x2 y2 x3 y3 x4 y4 (normalized)
    """
    with open(label_file, 'w') as f:
        for box in boxes:
            class_id, points = box
            coords = ' '.join([f"{x:.6f} {y:.6f}" for x, y in points])
            f.write(f"{class_id} {coords}\n")

def augment_obb_image(image, bboxes, img_height, img_width):
    """
    Apply augmentations to an image and update the corresponding OBBs.
    The bounding box points are normalized, so we will denormalize before augmenting.
    """
    # Denormalize the points to the image size for augmentation
    keypoints = []
    for bbox in bboxes:
        class_id, points = bbox
        denormalized_points = [(x * img_width, y * img_height) for x, y in points]
        keypoints.extend(denormalized_points)  # Flatten the list of points

    # Define your augmentation pipeline
    transform = A.Compose([
        A.HorizontalFlip(p=0.5),
        A.VerticalFlip(p=0.2),
        A.RandomBrightnessContrast(p=0.2),
        A.Rotate(limit=20, p=0.5),
    ], keypoint_params=A.KeypointParams(format='xy', remove_invisible=False))

    # Apply augmentation
    augmented = transform(image=image, keypoints=keypoints)

    # Clip keypoints to stay within image dimensions after augmentation
    def clip_keypoint(keypoint):
        x, y = keypoint
        x = max(0, min(x, img_width - 1))  # Ensure x is in [0, img_width]
        y = max(0, min(y, img_height - 1))  # Ensure y is in [0, img_height]
        return (x, y)

    clipped_keypoints = [clip_keypoint(kp) for kp in augmented['keypoints']]

    # Group the augmented keypoints back into their respective OBBs
    new_bboxes = []
    for i in range(0, len(clipped_keypoints), 4):  # Each bbox has 4 keypoints
        class_id = bboxes[i // 4][0]  # Class ID stays the same
        points = clipped_keypoints[i:i + 4]  # Extract the 4 keypoints

        # Normalize the points back to the image size
        normalized_points = [(x / img_width, y / img_height) for x, y in points]
        new_bboxes.append([class_id, normalized_points])

    return augmented['image'], new_bboxes

def augment_dataset(image_dir, label_dir, output_image_dir, output_label_dir, num_aug=5):
    """
    Augment a dataset of images and OBB labels in the custom format.
    image_dir: Directory where images are stored.
    label_dir: Directory where label files (.txt) are stored.
    output_image_dir: Directory where augmented images will be saved.
    output_label_dir: Directory where augmented label files will be saved.
    num_aug: Number of augmentations per image.
    """
    if not os.path.exists(output_image_dir):
        os.makedirs(output_image_dir)
    if not os.path.exists(output_label_dir):
        os.makedirs(output_label_dir)

    for image_file in os.listdir(image_dir):
        if image_file.endswith(".jpg") or image_file.endswith(".png"):
            image_path = os.path.join(image_dir, image_file)
            label_path = os.path.join(label_dir, image_file.replace(".jpg", ".txt").replace(".png", ".txt"))

            # Load the image
            image = cv2.imread(image_path)
            img_height, img_width = image.shape[:2]

            # Load the OBB labels
            bboxes = load_obb_labels(label_path)
            if len(bboxes) == 0:  # Skip if there are no bounding boxes
                continue

            # Perform augmentations
            for i in range(num_aug):
                augmented_image, augmented_bboxes = augment_obb_image(image, bboxes, img_height, img_width)

                if len(augmented_bboxes) == 0:  # Skip if there are no valid boxes after augmentation
                    continue

                # Save augmented image
                augmented_image_filename = f"{os.path.splitext(image_file)[0]}_aug_{i}.jpg"
                cv2.imwrite(os.path.join(output_image_dir, augmented_image_filename), augmented_image)

                # Save augmented labels
                augmented_label_filename = f"{os.path.splitext(image_file)[0]}_aug_{i}.txt"
                save_obb_labels(os.path.join(output_label_dir, augmented_label_filename), augmented_bboxes)

# Example usage:
image_dir = r"C:\Users\yoeri\OneDrive - De Haagse Hogeschool\Documenten\SM&R\Conveni\datasets\data2.2\valid\images"        # Folder with original images
label_dir = r"C:\Users\yoeri\OneDrive - De Haagse Hogeschool\Documenten\SM&R\Conveni\datasets\data2.2\valid\labels"      # Folder with YOLO format labels
output_image_dir = r"C:\Users\yoeri\OneDrive - De Haagse Hogeschool\Documenten\SM&R\Conveni\datasets\data2.3\valid\images"  # Folder to save augmented images
output_label_dir = r"C:\Users\yoeri\OneDrive - De Haagse Hogeschool\Documenten\SM&R\Conveni\datasets\data2.3\valid\labels"  # Folder to save augmented labels


# Augment the dataset (e.g., 5 augmentations per image)
augment_dataset(image_dir, label_dir, output_image_dir, output_label_dir, num_aug=5)
