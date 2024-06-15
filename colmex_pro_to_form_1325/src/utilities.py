import os.path


class Utilities:
    @staticmethod
    def get_file_extension(file_path: str):
        extension = os.path.splitext(file_path)
        if extension and extension[1] and len(extension[1]) > 1:
            return extension[1][1:]
        raise Exception(f"Failed to get the file extension for: {file_path}")

    @staticmethod
    def file_exists(file_path):
        return os.path.exists(file_path)
