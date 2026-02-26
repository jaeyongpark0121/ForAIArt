import os
import logging
from pathlib import Path
from PIL import Image
from rembg import remove

# 유지보수 및 디버깅을 위한 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class BatchImageProcessor:
    def __init__(self, target_size=(1024, 1024), bg_color=(255, 255, 255)):
        """
        초기화 메서드. 기본값은 1024x1024 크기와 흰색 배경입니다.
        추후 요구사항이 변경되어도 이 파라미터만 수정하면 됩니다.
        """
        self.target_size = target_size
        self.bg_color = bg_color
        self.valid_extensions = {'.png', '.jpg', '.jpeg', '.webp'}

    def process_directory(self, input_dir: str, output_dir: str, use_ai_bg_removal: bool = True):
        """
        지정된 폴더와 모든 하위 폴더를 탐색하여 이미지를 일괄 처리합니다.
        """
        input_path = Path(input_dir)
        output_path = Path(output_dir)

        if not input_path.exists():
            logging.error(f"입력 폴더를 찾을 수 없습니다: {input_dir}")
            return

        # rglob을 사용하여 하위 폴더 내의 모든 파일을 재귀적으로 탐색
        for img_path in input_path.rglob('*'):
            if img_path.is_file() and img_path.suffix.lower() in self.valid_extensions:
                self._process_single_image(img_path, input_path, output_path, use_ai_bg_removal)

    def _process_single_image(self, img_path: Path, base_input_path: Path, base_output_path: Path, use_ai_bg_removal: bool):
        """
        단일 이미지를 처리하고 기존 하위 폴더 구조를 유지하며 저장합니다.
        """
        try:
            # 기존 하위 폴더 경로 구조 계산
            relative_path = img_path.relative_to(base_input_path)
            out_path = base_output_path / relative_path
            out_path = out_path.with_suffix('.png') # 고품질을 위해 PNG로 통일

            # 결과물을 저장할 하위 폴더 생성
            out_path.parent.mkdir(parents=True, exist_ok=True)

            with Image.open(img_path) as img:
                img = img.convert("RGBA")

                # 1. AI 배경 제거 (필요한 경우)
                if use_ai_bg_removal:
                    img = remove(img)

                # 2. 비율을 유지하며 크기 조절 (피사체가 잘리지 않게 방지)
                img.thumbnail(self.target_size, Image.Resampling.LANCZOS)
                
                # 3. 목표 크기의 흰색 배경 캔버스 생성
                new_img = Image.new("RGBA", self.target_size, self.bg_color + (255,))
                
                # 4. 생성된 캔버스 정중앙에 이미지 배치
                paste_x = (self.target_size[0] - img.width) // 2
                paste_y = (self.target_size[1] - img.height) // 2
                new_img.paste(img, (paste_x, paste_y), img)
                
                # 5. 최종본을 RGB 모드로 변환(투명도 제거) 후 저장
                final_img = new_img.convert("RGB")
                final_img.save(out_path, format="PNG")
                
                logging.info(f"처리 완료: {relative_path}")

        except Exception as e:
            logging.error(f"이미지 처리 실패 [{img_path.name}]: {e}")

# ==========================================
# 실행부 (Entry Point)
# ==========================================
if __name__ == "__main__":
    # TODO: 실제 이미지가 있는 폴더 경로와 결과물을 저장할 폴더 경로를 입력하세요.
    INPUT_FOLDER = "./BeforeCrop"    # 원본 이미지가 있는 최상위 폴더
    OUTPUT_FOLDER = "./AfterCrop" # 완성된 이미지가 저장될 새 폴더
    
    # 클래스 인스턴스화 및 실행
    processor = BatchImageProcessor(target_size=(1024, 1024), bg_color=(255, 255, 255))
    
    # 이미 배경이 지워져 있고 크기와 배경색만 맞춰야 한다면 use_ai_bg_removal=False 로 설정하세요. (속도가 훨씬 빠릅니다)
    processor.process_directory(INPUT_FOLDER, OUTPUT_FOLDER, use_ai_bg_removal=True)
