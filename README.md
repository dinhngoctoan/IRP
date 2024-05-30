# IRP : Bài toán kết hợp vấn đề vận tải với vấn đề tồn kho
Mô tả:
### Đầu vào
Bài toán nhận dữ liệu đầu vào là số lượng địa điểm ( gồm 1 kho và n khách hàng), số lượng xe, tải trọng của xe, đối với kho thì đầu vào là lượng hàng vào kho hàng ngày và chi phí tồn kho của kho, đối với khách hàng thì có đầu vào là lượng hàng hiện có, hạn mức trên, hạn mức dưới của khách hàng, lượng tiêu thụ hàng ngày và chi phí tồn kho tại địa diểm đó
Cuối cùng là 1 ma trận khoảng cách giữa các điểm bao gồm kho và n khách hàng
### Đầu ra:
Một chuỗi hành trình của các xe cho mỗi chu kỳ cùng với lượng hàng cần giao tương ứng mỗi địa điểm dưới dạng " Địa điểm ( lượng hàng cần giao ) - ...." bắt đầu tại điểm 0 ( xuất phát từ kho ) và kết thúc tại điểm 0 ( về kho )
Chi phí tồn kho tại kho
Tổng chi phí tồn kho tại các địa điểm
Chi phí cho chuyến đi
Tổng tất cả các chi phí
### Công nghệ sử dụng:
Python 3.9
