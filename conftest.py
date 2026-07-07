"""File đánh dấu rootdir cho pytest.

Để trống có chủ đích: sự tồn tại của file này ở repo root giúp pytest
thêm root vào sys.path, nhờ đó tests/ import được app_utils dù chạy
bằng `pytest` trần hay `python -m pytest`.
"""
