class DefineOrder:
    def __init__(self):
        self.payment_methods = """
        - **Chuyển khoản ngân hàng Việt Nam**:
        - Ngân hàng: Sacombank  
        - Số tài khoản: 060296156232  
        - Chủ tài khoản: TRAN THI THUY VY  
        - [Mã QR thanh toán](#) (quét bằng app ngân hàng hỗ trợ Napas 247)

        - **Chuyển khoản ngân hàng Nhật Bản**:
        - Ngân hàng: Yucho Ginko (ゆうちょ銀行)  
        - Số tài khoản: 15540-31023011  
        - Tên tài khoản: チェン スアン ティン
        """

        self.shipping_policy = """
            - Miễn phí vận chuyển toàn quốc cho đơn hàng từ 9000 yên trở lên hoặc đơn hàng có 10 trang size 20*20.
            - Với đơn hàng có tranh size 30*40 bạn sẽ được giảm giá 300 yên.
            - Với đơn hàng có tranh size 40*50 bạn sẽ được giảm giá 500 yên.
	        (Lưu ý: Nhập mã mới được giảm giá)
        """

        self.delivery_info = """
            - **Thời gian xử lý đơn hàng**: Cuối ngày.
            - **Thời gian giao hàng**:
                Sau khi đơn hàng xác nhận tiệm sẽ gửi hàng, khoảng 2-4 ngày bạn sẽ nhận đc hàng.
        """

        self.order_steps = """
            1. **Chọn tranh yêu thích** và nhấn nút *"Thêm vào giỏ hàng"*.
            2. Vào *giỏ hàng* để kiểm tra sản phẩm và số lượng.
            3. Nhấn *"Thanh toán"*, điền đầy đủ thông tin giao hàng.
            4. Xác nhận đơn hàng và và tiến hành thanh toán (bạn có thể thanh toán sau, trong vòng 1 tuần, nếu sau 1 tuần chưa thanh toán đơn hàng sẽ tự động hủy).
            5. Sau khi thanh toán xong bạn tải ảnh lên và đơn hàng sẽ chuyển sang trạng thái "ĐÃ THANH TOÁN"
            6. Tiệm sẽ xác nhận và vận chuyển đến bạn trong thời gian sớm nhất.
        """