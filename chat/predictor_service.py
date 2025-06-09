import joblib
import os
import pandas as pd

# Lớp này sẽ quản lý việc tải và sử dụng model (Singleton pattern)
class PricePredictor:
    def __init__(self):
        self.model = None
        self.load_model()
    
    def load_model(self):
        """Tải model từ file .joblib vào bộ nhớ."""
        model_path = 'chat/model/best_model_xgb.joblib'
        try:
            self.model = joblib.load(model_path)
            print("ML Model loaded successfully!")
        except FileNotFoundError:
            print(f"Error: Model file not found at {model_path}")
            self.model = None

    def predict(self, input_data):
        """
        Thực hiện dự đoán dựa trên dữ liệu đầu vào.
        `input_data` nên là một dictionary.
        """
        if self.model is None:
            return "Model is not loaded."
        
        try:
            print(input_data)
            # ----- QUAN TRỌNG NHẤT ------
            # Dữ liệu đầu vào phải được chuyển đổi thành định dạng mà model mong đợi.
            # Thường là một Pandas DataFrame với các cột và thứ tự chính xác.
            fields = ['storage_max_support', 'storage_gb', 'display_width', 'cpu_threads', 'cpu_cores', 
                    'ram_speed', 'cpu_speed', 'ram_storage', 'ram_slots', 'battery_capacity', 
                    'display_height', 'laptop_sang_tao_noi_dung', 'do_hoa_ky_thuat', 'cao_cap_sang_trong', 
                    'material', 'manufacturer', 'ram_type', 'os_version', 'laptop_color', 'vga_brand', 'laptop_camera', 'cpu_brand']
            
            input_df = pd.DataFrame([input_data], columns=fields)
            print(input_df)
            prediction = self.model.predict(input_df)
            return prediction[0]

        except Exception as e:
            return f"Error: {e}"

# Tạo một instance duy nhất của class để sử dụng trong toàn bộ ứng dụng
predictor = PricePredictor()
