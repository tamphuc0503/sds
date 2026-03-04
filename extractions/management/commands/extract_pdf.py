import os
import re
import boto3
from botocore.config import Config
from django.core.management.base import BaseCommand
import re
import fitz
import numpy as np
from pymupdf import Page
from sklearn.cluster import DBSCAN
from sklearn.neighbors import NearestNeighbors


class Command(BaseCommand):
    help = "Extract a sds file"

    def add_arguments(self, parser):
        parser.add_argument("from", nargs="?", type=int)
        parser.add_argument("to", nargs="?", type=bool)

    def handle(self, *args, **options):
        worker_name = "extract_pdf"
        file_path = 's1/00/00/c29fb4e1593b6d13af61b19666611ef6.pdf'
        self._process_file(file_path)
        
    def _get_s3_client(self):
        return boto3.client(
            "s3",
            endpoint_url="https://usc1.contabostorage.com",
            aws_access_key_id="f35256d14c2a22f4648bce44896529d8",
            aws_secret_access_key="7672dbe85d3e540b7c62ff6df5704ef3",
            region_name="usc1",
            config=Config(s3={"addressing_style": "path"}),  # important for Contabo
        )
 
    def download_file_from_s3(
        self, s3_file_path, local_file_path=None, bucket_name="sds"
    ):
        """
        Download a file from S3 Contabo storage.

        Args:
            s3_file_path: The path/key of the file in S3 (e.g., 's1/00/00/0293a0ea54eb69d6b750eab79334288b.pdf')
            local_file_path: Optional local path to save the file. If not provided, saves to current directory with same filename
            bucket_name: The S3 bucket name (default: 'sds')

        Returns:
            str: The local file path where the file was saved

        Example:
            # Download to current directory
            self.download_file_from_s3('s1/00/00/0293a0ea54eb69d6b750eab79334288b.pdf')

            # Download to specific path
            self.download_file_from_s3('s1/00/00/0293a0ea54eb69d6b750eab79334288b.pdf', '/tmp/myfile.pdf')
        """        

        # If no local path provided, use the filename from S3 path
        if local_file_path is None:
            local_file_path = os.path.basename(s3_file_path)

        # If local path existed, use the local_file_path
        if os.path.exists(local_file_path):
            return local_file_path
        
        # Create directory if it doesn't exist
        local_dir = os.path.dirname(local_file_path)
        if local_dir and not os.path.exists(local_dir):
            os.makedirs(local_dir, exist_ok=True)

        try:
            # Download the file
            self.stdout.write(
                f"Downloading {s3_file_path} from bucket '{bucket_name}'..."           
            )
            s3 = self._get_s3_client()
            s3.download_file(bucket_name, s3_file_path, local_file_path)
            self.stdout.write(
                self.style.SUCCESS(f"Successfully downloaded to {local_file_path}")
            )
            return local_file_path

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Error downloading {s3_file_path}: {e}")
            )
            raise          
             
    def _process_file(self, file_path):
        try:
            # Download file from S3
            local_file_path = self.download_file_from_s3(file_path)
            local_file_path = "c29fb4e1593b6d13af61b19666611ef6.pdf"
            lines, page_width, page_height = extract_first_page_lines_precise(local_file_path)
            final = full_sds_pipeline(lines, page_width=page_width,page_height=page_height)            
            return final
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error downloading {file_path}: {e}"))



# ============================================================
# CONFIG
# ============================================================

ANCHOR_PATTERN = re.compile(
    r"(Product name|Company)",
    re.IGNORECASE
)

MIN_SAMPLES = 2


# ============================================================
# UTILITIES
# ============================================================

def normalize_bbox(bbox, page_width, page_height):
    x0, y0, x1, y1 = bbox
    return [
        x0 / page_width,
        y0 / page_height,
        x1 / page_width,
        y1 / page_height
    ]


def compute_center(bbox):
    x0, y0, x1, y1 = bbox
    return ( (x0 + x1) / 2, (y0 + y1) / 2 )


def normalize_text(text):
    text = text.replace("\t", " ")
    text = re.sub(r"\s{2,}", " ", text)
    return text.strip()


# ============================================================
# STEP 1 — DBSCAN LAYOUT CLUSTERING
# ============================================================

def estimate_eps(features, k=5):
    neigh = NearestNeighbors(n_neighbors=min(k, len(features)))
    neigh.fit(features)
    distances, _ = neigh.kneighbors(features)
    return np.percentile(distances[:, -1], 85)


def dbscan_layout_clustering(lines, page_width, page_height):

    features = []
    for line in lines:
        norm_bbox = normalize_bbox(
            line["bbox"], page_width, page_height
        )
        x_center = (norm_bbox[0] + norm_bbox[2]) / 2
        y_center = (norm_bbox[1] + norm_bbox[3]) / 2
        features.append([x_center, y_center])

    features = np.array(features)

    if len(features) < 2:
        return {0: lines}

    eps = estimate_eps(features)

    clustering = DBSCAN(
        eps=eps,
        min_samples=MIN_SAMPLES
    ).fit(features)

    clusters = {}
    for label, line in zip(clustering.labels_, lines):
        clusters.setdefault(label, []).append(line)

    return clusters


# ============================================================
# STEP 2 — COLUMN DETECTION
# ============================================================

def detect_columns(cluster, page_width):

    # Detect anchors first
    anchors = []
    for line in cluster:
        if ANCHOR_PATTERN.search(line["text"]):
            x_center = compute_center(line["bbox"])[0] / page_width
            anchors.append({
                "text": line["text"],
                "x": x_center,
                "bbox": line["bbox"]
            })

    # Sort anchors left → right
    anchors = sorted(anchors, key=lambda a: a["x"])

    return anchors


# ============================================================
# STEP 3 — ANCHOR DETECTION
# ============================================================

def extract_anchor_label(text):
    match = ANCHOR_PATTERN.search(text)
    if match:
        return match.group(0).strip()
    return None


# ============================================================
# STEP 4 — NEAREST ANCHOR ASSIGNMENT
# ============================================================

def assign_lines_to_anchors(cluster, anchors, page_width):

    if not anchors:
        return {}

    anchor_map = {
        anchor["text"]: [] for anchor in anchors
    }

    for line in cluster:

        label = extract_anchor_label(line["text"])
        if label:
            # Skip anchor lines themselves
            continue

        x_center = compute_center(line["bbox"])[0] / page_width

        # Find nearest anchor horizontally
        nearest = min(
            anchors,
            key=lambda a: abs(x_center - a["x"])
        )

        anchor_map[nearest["text"]].append(line)

    return anchor_map


# ============================================================
# STEP 5 — VERTICAL MERGE
# ============================================================

def vertical_merge(anchor_map):

    results = []

    for anchor, lines in anchor_map.items():

        # Sort top → bottom
        lines = sorted(
            lines,
            key=lambda l: l["bbox"][1]
        )

        merged_text = []
        buffer = ""

        for line in lines:
            text = normalize_text(line["text"])

            if not buffer:
                buffer = text
                continue

            # If previous line does not end sentence → continue
            if not re.search(r"[.!?]$", buffer):
                buffer += " " + text
            else:
                merged_text.append(buffer)
                buffer = text

        if buffer:
            merged_text.append(buffer)

        final_text = " ".join(merged_text).strip()

        if final_text:
            results.append(
                f"{normalize_text(anchor)} {final_text}"
            )

    return results


def extract_first_page_lines_precise(pdf_path):

    doc = fitz.open(pdf_path)
    page = doc[0]

    page_width = page.rect.width
    page_height = page.rect.height

    text_dict = page.get_text("dict")

    lines = []

    for block in text_dict["blocks"]:
        if "lines" not in block:
            continue

        for line in block["lines"]:
            spans = line["spans"]

            if not spans:
                continue

            text = "".join(span["text"] for span in spans).strip()
            if not text:
                continue

            x0 = min(span["bbox"][0] for span in spans)
            y0 = min(span["bbox"][1] for span in spans)
            x1 = max(span["bbox"][2] for span in spans)
            y1 = max(span["bbox"][3] for span in spans)

            lines.append({
                "text": text,
                "page": 0,
                "bbox": [x0, y0, x1, y1],
                "x0": x0, "y0": y0, "x1": x1,"y1": y1
            })
    blocks = sort_blocks(lines)
    paragraphs = group_paragraphs(blocks)
    _draw_matrix(page, paragraphs)
    
    doc.save("output_document.pdf")
    return lines, page_width, page_height

def sort_blocks(blocks):
    return sorted(blocks, key=lambda b: (b["page"], b["y0"], b["x0"]))

def group_paragraphs(blocks, y_threshold=4, x_threshold=5):
    paragraphs = []
    current_para = blocks[0]

    for block in blocks[1:]:
        same_page = block["page"] == current_para["page"]
        vertical_gap = abs(block["y0"] - current_para["y1"])
        same_column = abs(block["x0"] - current_para["x0"]) < x_threshold

        if same_page and vertical_gap < y_threshold and same_column:
            current_para["text"] += " " + block["text"]
            current_para["y1"] = block["y1"]
        else:
            paragraphs.append(current_para)
            current_para = block

    paragraphs.append(current_para)
    return paragraphs

# ============================================================
# FULL PIPELINE
# ============================================================

def full_sds_pipeline(lines, page_width, page_height):

    final_output = []

    clusters = dbscan_layout_clustering(
        lines, page_width, page_height
    )

    # Sort clusters top → bottom
    sorted_clusters = sorted(
        clusters.values(),
        key=lambda c: min(l["bbox"][1] for l in c)
    )

    for cluster in sorted_clusters:

        anchors = detect_columns(cluster, page_width)

        if not anchors:
            continue

        anchor_map = assign_lines_to_anchors(
            cluster, anchors, page_width
        )

        merged = vertical_merge(anchor_map)

        final_output.extend(merged)

    return final_output


def _draw_matrix(page: Page, blocks):
    page.draw_rect(page.rect, color=(0, 1, 0), width=1)

    for b in blocks:
        rect = fitz.Rect(b['x0'], b['y0'], b['x1'], b['y1'])
        page.draw_rect(rect, color=(0, 1, 0), width=1)
        # page.insert_text(
        #     (int(b['x0']), int(b.y0)),
        #     f"r:{b.rowid},c:{b.colid}",
        #     fontsize=10,
        #     color=(1, 0, 0),
        # )
        # page.insert_text(
        #     (int(b.x), int(b.y)),
        #     f"{int(b.x)},{int(b.y)}",
        #     fontsize=10,
        #     color=(1, 0, 0),
        # )
        # page.insert_text(
        #     (int(b.x1), int(b.y1)),
        #     f"{int(b.x1)},{int(b.y1)},c:{b.colid},r:{b.rowid}",
        #     fontsize=10,
        #     color=(1, 0, 0),
        # )