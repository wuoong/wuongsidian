import os
import json

class ConfigManager:
    """本地配置文件管理器，用于记录用户偏好和历史记录"""
    def __init__(self, config_file="settings.json"):
        # 将配置文件保存在应用根目录下
        self.config_file = config_file
        self.config_data = self._load_config()

    def _load_config(self):
        """加载本地配置文件"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"配置文件读取失败: {e}")
                return {}
        return {}

    def _save_config(self):
        """将当前配置持久化到本地"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config_data, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"配置文件保存失败: {e}")

    def get_last_vault(self):
        """获取用户最后一次打开的仓库路径"""
        return self.config_data.get("last_vault", "")

    def set_last_vault(self, path):
        """更新最后一次打开的仓库路径并保存"""
        self.config_data["last_vault"] = path
        self._save_config()

    # ================= 新增 API Key 管理 =================
    def get_api_key(self):
        """获取用户本地保存的 API Key"""
        return self.config_data.get("api_key", "")

    def set_api_key(self, api_key):
        """保存 API Key 到本地"""
        self.config_data["api_key"] = api_key
        self._save_config()