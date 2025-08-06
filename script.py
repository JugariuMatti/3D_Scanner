import os
import subprocess

# === CONFIG ===
IMAGE_DIR = r"C:\Users\matti\Desktop\Licenta\Images"
PROJECT_DIR = r"C:\Users\matti\Desktop\Licenta\Output"
DB_PATH = os.path.join(PROJECT_DIR, "database.db")
SPARSE_DIR = os.path.join(PROJECT_DIR, "sparse")
DENSE_DIR = os.path.join(PROJECT_DIR, "dense")
FINAL_PLY = os.path.join(PROJECT_DIR, "final_model.ply")

# === PREPARE FOLDERS ===
os.makedirs(PROJECT_DIR, exist_ok=True)
os.makedirs(SPARSE_DIR, exist_ok=True)
os.makedirs(DENSE_DIR, exist_ok=True)

# === STEP 1: Feature Extraction ===
subprocess.run([
    "colmap", "feature_extractor",
    "--database_path", DB_PATH,
    "--image_path", IMAGE_DIR
], check=True)

# === STEP 2: Matching ===
subprocess.run([
    "colmap", "sequential_matcher",
    "--database_path", DB_PATH
], check=True)

# === STEP 3: Sparse Reconstruction ===
subprocess.run([
    "colmap", "mapper",
    "--database_path", DB_PATH,
    "--image_path", IMAGE_DIR,
    "--output_path", SPARSE_DIR
], check=True)

# === STEP 4: Undistort Images ===
subprocess.run([
    "colmap", "image_undistorter",
    "--image_path", IMAGE_DIR,
    "--input_path", os.path.join(SPARSE_DIR, "0"),
    "--output_path", DENSE_DIR,
    "--output_type", "COLMAP"
], check=True)

# === STEP 5: Dense Reconstruction with PatchMatch ===
subprocess.run([
    "colmap", "patch_match_stereo",
    "--workspace_path", DENSE_DIR,
    "--workspace_format", "COLMAP",
    "--PatchMatchStereo.geom_consistency", "true"
], check=True)

# === STEP 6: Fusion ===
subprocess.run([
    "colmap", "stereo_fusion",
    "--workspace_path", DENSE_DIR,
    "--workspace_format", "COLMAP",
    "--input_type", "geometric",
    "--output_path", FINAL_PLY
], check=True)

print(f"✅ Final 3D model exported as dense PLY: {FINAL_PLY}")
