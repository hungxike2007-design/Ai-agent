BỘ GIÁO DỤC VÀ ĐÀO TẠO
TRƯỜNG ĐẠI HỌC CÔNG NGHỆ TP. HCM

BÁO CÁO ĐỒ ÁN CƠ SỞ

AI Agent phân tích dữ liệu Excel và sinh báo cáo tự động

Ngành:	CÔNG NGHỆ THÔNG TIN

Giảng viên hướng dẫn: KS. Phạm Văn Khải
Nhóm Sinh viên thực hiện:
Tên	Lớp	MSSV
	Nguyễn Xuân Huy	23DTHB7	2180600865
	Nguyễn Anh Huy	23DTHB7	2180600840
	Phạm Thanh Hùng	23DTHB7	218060

TP. Hồ Chí Minh, 2026

LỜI CẢM ƠN
Kính thưa Thầy,
Lời đầu tiên chúng em xin gửi lời cảm ơn chân thành nhất đến Thầy Phạm Văn Khải đã dành thời gian quý báu để lắng nghe và đánh giá bài báo cáo của chúng em.
Sự hỗ trợ và phản hồi từ Thầy không chỉ là nguồn động viên lớn lao mà còn là cơ hội để chúng em có cơ sở để hoàn thiện công việc của mình. Thầy đã mang đến những góp ý xây dựng và sâu sắc, giúp chúng em hiểu rõ hơn về chủ đề và cách thức cải thiện nội dung.
Chúng em không thể không nhắc đến sự đóng góp của Thầy, người đã giúp chúng em vượt qua những thách thức và phát triển từng ngày. Sự hỗ trợ và khích lệ của Thầy đã làm cho hành trình nghiên cứu và trình bày của chúng em trở nên ý nghĩa và giá trị hơn bao giờ hết.
Cuối cùng, chúng em xin kính chúc Thầy sức khỏe và thành công trong công việc nghiên cứu và giảng dạy, cũng như trong mọi lĩnh vực cuộc sống. Hãy tiếp tục lan tỏa sự kiến thức và sự nhiệt huyết của mình đến những người xung quanh và là nguồn động viên cho những thế hệ tương lai.
Xin một lần nữa, lời cảm ơn chân thành từ tận đáy lòng của chúng em!

MỤC LỤC
LỜI CẢM ƠN	i
MỤC LỤC	ii
DANH MỤC HÌNH ẢNH	v
DANH MỤC BẢNG BIỂU	vii
LỜI MỞ ĐẦU	1
1. Lý do chọn đề tài	1
2. Mục đích nghiên cứu	1
3. Ý nghĩa của việc nghiên cứu	1
4. Kết cấu đề tài:	1
CHƯƠNG 1: TỔNG QUAN VÀ CƠ SỞ LÝ THUYẾT	2
1.1.	Khảo sát hiện trạng	2
1.2.	Nhiệm vụ của việc nghiên cứu	2
1.3.	Đối tượng và khách thể nghiên cứu	2
1.4.	Phương pháp và phạm vi nghiên cứu	2
1.4.1.	Phương pháp nghiên cứu	2
1.4.2.	Phạm vi nghiên cứu	3
1.5.	Giới thiệu ngôn ngữ, framework, thư viện, nền tảng	3
1.5.1.	Khái niệm ngôn ngữ Python	3
1.5.2.	Tìm hiểu thư viện Pandas và Xử lý dữ liệu	4
1.5.3.	Tìm hiểu thư viện Matplotlib và Plotly	5
1.5.4.	Tìm hiểu về AI Agent và LLM	5
CHƯƠNG 2: PHÂN TÍCH VÀ THIẾT KẾ	8
2.1.	Kiến trúc hệ thống AI Agent	8
2.2.	Quy trình làm sạch và phân tích dữ liệu (Data Pipeline)	8
2.3.	Các mô hình dữ liệu (UseCase)	10
2.3.1.	Mô hình UseCase tổng quát	10
2.3.2.	Mô hình UseCase tải tệp Excel lên	11
2.3.3.	Mô hình UseCase làm sạch dữ liệu tự động	11
2.3.4.	Mô hình UseCase sinh biểu đồ tự động	11
2.3.5.	Mô hình UseCase sinh báo cáo phân tích bằng AI	12
2.4.	Mô hình Sequence Diagram	14
2.4.1.	Sequence Diagram xử lý tệp Excel	14
2.4.2.	Sequence Diagram quá trình phân tích bằng LLM	14
2.5.	Thiết kế giao diện người dùng	16
2.5.1.	Giao diện trang chủ (Dashboard)	16
2.5.2.	Giao diện tải tệp dữ liệu lên	17
2.5.3.	Giao diện kết quả làm sạch dữ liệu	17
2.5.4.	Giao diện hiển thị biểu đồ phân tích	18
2.5.5.	Giao diện báo cáo tự động (Chatbot/Insight)	18
CHƯƠNG 3: KẾT LUẬN	22
3.1.	Ưu điểm	22
3.2.	Nhược điểm	22
3.3.	Hướng phát triển toàn diện	22
TÀI LIỆU THAM KHẢO	23

LỜI MỞ ĐẦU
1. Lý do chọn đề tài
Trong kỷ nguyên số, dữ liệu đóng vai trò quan trọng trong việc đưa ra các quyết định chiến lược của doanh nghiệp. Hàng ngày, một khối lượng lớn dữ liệu được lưu trữ và xử lý dưới định dạng Excel. Tuy nhiên, việc phân tích dữ liệu theo cách thủ công đòi hỏi nhiều thời gian, công sức và phụ thuộc vào trình độ của người phân tích. Điều này dẫn đến sự chậm trễ trong việc đưa ra quyết định hoặc sai sót trong quá trình xử lý dữ liệu.
Sự ra đời của Trí tuệ nhân tạo (AI), đặc biệt là các mô hình ngôn ngữ lớn (LLM) và AI Agent, đã mở ra hướng đi mới giúp tự động hóa quá trình xử lý, làm sạch và phân tích dữ liệu. Từ đó, ý tưởng xây dựng một "AI Agent phân tích dữ liệu Excel và sinh báo cáo tự động" được hình thành, với mục tiêu giúp người dùng không có nền tảng chuyên môn sâu về khoa học dữ liệu vẫn có thể hiểu và rút ra những hiểu biết (insights) giá trị từ dữ liệu của mình.

2. Mục đích nghiên cứu
Xây dựng một công cụ (AI Agent) có khả năng tự động hóa các bước sau:
- Tiếp nhận và đọc dữ liệu từ tệp Excel.
- Tự động làm sạch dữ liệu (loại bỏ dữ liệu rác, xử lý giá trị thiếu, chuẩn hóa định dạng).
- Tự động vẽ các biểu đồ phù hợp với từng loại dữ liệu (Pie chart, Bar chart, Line chart, Histogram).
- Ứng dụng LLM để sinh báo cáo phân tích dữ liệu dựa trên các số liệu và biểu đồ thu thập được, đồng thời tương tác với người dùng dưới dạng hỏi-đáp.

3. Ý nghĩa của việc nghiên cứu
Kết quả của nghiên cứu mang ý nghĩa:
- Về mặt lý thuyết: Tìm hiểu sâu về quy trình khai phá dữ liệu (Data Mining), làm sạch dữ liệu (Data Cleaning) và ứng dụng các mô hình AI Agent/LLM vào thực tiễn. Nâng cao kỹ năng lập trình Python và sử dụng các thư viện phổ biến (Pandas, Matplotlib, Plotly).
- Về mặt thực tiễn: Cung cấp một công cụ hữu ích giúp người dùng tiết kiệm thời gian phân tích số liệu, tạo báo cáo tự động và tăng hiệu suất làm việc.

4. Kết cấu đề tài:
LỜI MỞ ĐẦU
CHƯƠNG 1: TỔNG QUAN VÀ CƠ SỞ LÝ THUYẾT
CHƯƠNG 2: PHÂN TÍCH VÀ THIẾT KẾ
CHƯƠNG 3: KẾT LUẬN

CHƯƠNG 1: TỔNG QUAN VÀ CƠ SỞ LÝ THUYẾT
1.1. Khảo sát hiện trạng
Hiện nay, Excel là công cụ phổ biến nhất để quản lý dữ liệu trong các doanh nghiệp vừa và nhỏ. Tuy nhiên, khi dữ liệu lớn dần, việc kiểm tra lỗi, lọc dữ liệu rác (dòng trống, dữ liệu trùng lặp, sai định dạng) trở nên khó khăn. Hơn nữa, việc tạo các biểu đồ phân tích và viết báo cáo đánh giá xu hướng dữ liệu đòi hỏi người dùng phải thao tác nhiều bước thủ công. Các công cụ BI (Business Intelligence) như PowerBI, Tableau lại đòi hỏi người dùng phải có kiến thức chuyên môn và thời gian đào tạo nhất định.
Việc tích hợp AI Agent vào quy trình xử lý dữ liệu sẽ giúp thu hẹp khoảng cách giữa người dùng cơ bản và các hệ thống phân tích dữ liệu chuyên sâu. AI Agent đóng vai trò như một chuyên gia phân tích dữ liệu ảo, tự động hóa toàn bộ quá trình từ làm sạch đến đưa ra các nhận định chiến lược.

1.2. Nhiệm vụ của việc nghiên cứu
Phần mềm này được tạo ra nhằm đơn giản hóa quy trình phân tích dữ liệu Excel cho người dùng. Ứng dụng tích hợp sẵn các tập tin kịch bản (scripts) xử lý dữ liệu mạnh mẽ, kết hợp cùng giao diện người dùng trực quan và AI để sinh ra kết luận. Người dùng chỉ cần tải tệp Excel lên, hệ thống sẽ tự động đưa ra kết quả phân tích cùng các biểu đồ trực quan nhất.

1.3. Đối tượng và khách thể nghiên cứu
- Đối tượng nghiên cứu: AI Agent, LLM, quy trình làm sạch dữ liệu và tạo biểu đồ tự động.
- Khách thể nghiên cứu: Các cá nhân, nhân viên văn phòng, quản lý doanh nghiệp có nhu cầu phân tích dữ liệu Excel thường xuyên nhưng thiếu công cụ tự động hóa hoặc chuyên môn sâu về Data Analysis.

1.4. Phương pháp và phạm vi nghiên cứu
1.4.1. Phương pháp nghiên cứu
- Nghiên cứu tài liệu: Tìm hiểu về các thư viện xử lý dữ liệu của Python (Pandas), trực quan hóa dữ liệu (Matplotlib, Plotly), các tài liệu về cách tích hợp API của các mô hình ngôn ngữ lớn (OpenAI GPT, v.v.).
- Nghiên cứu thực nghiệm: Xây dựng các hàm `deep_clean_data`, `generate_auto_chart`, đánh giá tính hiệu quả khi xử lý các tập dữ liệu rác mô phỏng thực tế.

1.4.2. Phạm vi nghiên cứu
- Phạm vi xử lý dữ liệu: Hệ thống hiện tập trung vào các tệp tin định dạng `.xlsx`, `.xls` và `.csv`. Các bước làm sạch dữ liệu tập trung vào việc loại bỏ cột/dòng rỗng, dòng trùng lặp, chuẩn hóa kiểu dữ liệu, loại bỏ ký tự đặc biệt và cảnh báo ngoại lệ (outlier).
- Phạm vi AI: Sử dụng AI để nhận diện ngữ cảnh dữ liệu, sinh text mô tả các insight, trả lời câu hỏi của người dùng dựa trên bộ dữ liệu được tải lên.

1.5. Giới thiệu ngôn ngữ, framework, thư viện, nền tảng
1.5.1. Khái niệm ngôn ngữ Python
Python là ngôn ngữ lập trình kịch bản mã nguồn mở, đa dụng và rất phổ biến trong lĩnh vực Khoa học Dữ liệu (Data Science) và Trí tuệ Nhân tạo (AI). Python có cú pháp đơn giản, dễ đọc, được hỗ trợ bởi hệ sinh thái thư viện phong phú, giúp các nhà phát triển dễ dàng thực hiện các thuật toán phức tạp về làm sạch dữ liệu và tích hợp mô hình AI.

1.5.2. Tìm hiểu thư viện Pandas và Xử lý dữ liệu
Pandas là một thư viện mã nguồn mở cung cấp các cấu trúc dữ liệu hiệu suất cao và các công cụ phân tích dữ liệu cho ngôn ngữ Python. DataFrame của Pandas cho phép thao tác với dữ liệu dạng bảng tương tự như Excel nhưng linh hoạt hơn rất nhiều thông qua code.
Ứng dụng trong đề tài: Pandas được sử dụng để đọc tệp Excel, truy xuất cột, dòng, thực hiện các thao tác xử lý dữ liệu tự động như: drop_duplicates(), fillna(), thay đổi kiểu dữ liệu (to_numeric), thay thế văn bản, v.v.

1.5.3. Tìm hiểu thư viện Matplotlib và Plotly
- Matplotlib: Là một thư viện vẽ đồ thị cơ bản trong Python. Trong dự án, nó được sử dụng thông qua chế độ 'Agg' (không giao diện) để render các biểu đồ tĩnh tĩnh (PNG) phức tạp kèm theo Legend Panel chuyên nghiệp (chú thích dữ liệu).
- Plotly: Là thư viện vẽ biểu đồ tương tác cao. Các biểu đồ tạo ra bởi Plotly có thể zoom, hover để xem số liệu trực tiếp trên trình duyệt.

1.5.4. Tìm hiểu về AI Agent và LLM
LLM (Large Language Model) là các mô hình AI có khả năng hiểu và sinh ngôn ngữ tự nhiên. AI Agent là một hệ thống sử dụng LLM làm trung tâm bộ não để lập kế hoạch, sử dụng công cụ (như mã Python, thư viện Pandas) để giải quyết các vấn đề mà người dùng yêu cầu. Trong đề tài, AI Agent sẽ đọc bản tóm tắt dữ liệu (schema, summary stats) và sinh ra một bản báo cáo bằng văn bản tự nhiên để gửi cho người dùng.

CHƯƠNG 2: PHÂN TÍCH VÀ THIẾT KẾ
2.1. Kiến trúc hệ thống AI Agent
Hệ thống được thiết kế theo kiến trúc Client-Server. 
- Client (Frontend): Cung cấp giao diện web để người dùng tải tệp Excel và gửi yêu cầu phân tích.
- Server (Backend): Tiếp nhận tệp, sử dụng module xử lý dữ liệu (Pandas) để chuẩn hóa cấu trúc tệp, làm sạch. Sau đó dữ liệu được truyền sang module trực quan hóa (Matplotlib/Plotly) để tạo biểu đồ. Cuối cùng, thông tin dữ liệu được gửi đến AI Agent (thông qua API) để sinh báo cáo phân tích tổng quan.

2.2. Quy trình làm sạch và phân tích dữ liệu (Data Pipeline)
Hệ thống tích hợp kỹ năng Deep Clean Data với 8 bước xử lý rác:
1. Chuẩn hóa cấu trúc Excel (loại bỏ tiêu đề thừa).
2. Xóa các cột rỗng 100% hoặc cột "Unnamed".
3. Xóa các dòng rỗng (hơn 80% cột trống).
4. Xóa dòng trùng lặp hoàn toàn.
5. Phát hiện và xóa header lặp trong data.
6. Chuẩn hóa text (xóa khoảng trắng thừa, xử lý giá trị nan).
7. Sửa các lỗi encoding và loại bỏ ký tự đặc biệt.
8. Tự động chuyển đổi kiểu dữ liệu (từ object sang numeric) và phát hiện giá trị ngoại lệ (outlier).
Sau khi dữ liệu "sạch", hệ thống kích hoạt hàm sinh biểu đồ tự động để phân tích cấu trúc cột (có cột ngày không, có bao nhiêu cột số, số lượng nhóm trong cột text) nhằm quyết định vẽ loại biểu đồ phù hợp nhất (Pie, Line, Bar, Hist).

2.3. Các mô hình dữ liệu (UseCase)
2.3.1. Mô hình UseCase tổng quát
Người dùng (User) có thể tương tác với các UseCase: Tải tệp dữ liệu lên, Xem đề xuất làm sạch dữ liệu, Xem biểu đồ trực quan, Xem báo cáo AI tự động, Đặt câu hỏi truy vấn dữ liệu.

2.3.2. Mô hình UseCase tải tệp Excel lên
Người dùng chọn tệp (.xlsx, .csv) từ máy tính. Hệ thống kiểm tra định dạng và tiến hành đọc dữ liệu sơ bộ.

2.3.3. Mô hình UseCase làm sạch dữ liệu tự động
Hệ thống hiển thị danh sách các vấn đề của dữ liệu (NULL, giá trị âm, rác). Người dùng có thể nhấn nút "Tự động làm sạch" hoặc áp dụng làm sạch chuyên sâu (deep_clean).

2.3.4. Mô hình UseCase sinh biểu đồ tự động
Dựa vào bộ dữ liệu đã làm sạch, hệ thống nhận diện các cột định lượng và định tính để vẽ ra biểu đồ phản ánh đúng nhất xu hướng của dữ liệu.

2.3.5. Mô hình UseCase sinh báo cáo phân tích bằng AI
Hệ thống gửi tóm tắt dữ liệu (schema, phân phối, top giá trị) cho LLM. LLM sinh ra nội dung nhận xét, kết luận và đề xuất hành động.

2.4. Mô hình Sequence Diagram
2.4.1. Sequence Diagram xử lý tệp Excel
Người dùng -> Web Interface: Upload tệp
Web Interface -> Backend: Gửi tệp
Backend -> Data Processor: Đọc tệp bằng Pandas và làm sạch
Data Processor -> Backend: Trả về DataFrame sạch & báo cáo làm sạch
Backend -> Chart Generator: Vẽ biểu đồ tự động
Chart Generator -> Backend: Trả về đường dẫn ảnh biểu đồ
Backend -> Web Interface: Hiển thị kết quả làm sạch & biểu đồ

2.4.2. Sequence Diagram quá trình phân tích bằng LLM
Backend -> AI Agent: Gửi ngữ cảnh dữ liệu (Metadata) + Yêu cầu phân tích
AI Agent -> OpenAI/LLM API: Gửi Prompt
OpenAI/LLM API -> AI Agent: Trả về Response (Báo cáo phân tích)
AI Agent -> Backend: Format dữ liệu JSON/Markdown
Backend -> Web Interface: Hiển thị báo cáo cho người dùng

2.5. Thiết kế giao diện website
2.5.1. Giao diện trang chủ
Giới thiệu tổng quan về tính năng của AI Agent phân tích dữ liệu, cung cấp nút để người dùng bắt đầu tải tệp lên.

2.5.2. Giao diện tải tệp và xem trước dữ liệu
Vùng Drag & Drop để tải tệp. Phía dưới hiển thị bảng xem trước (Preview) một số dòng dữ liệu của tệp Excel để người dùng đối chiếu.

2.5.3. Giao diện kết quả làm sạch dữ liệu
Hiển thị danh sách các cảnh báo dữ liệu lỗi. Các actions (Xóa cột, Xóa dòng rỗng, Điền giá trị trung bình) được liệt kê để người dùng tương tác, hoặc có nút "Tự động sửa lỗi (Auto Clean)".

2.5.4. Giao diện hiển thị biểu đồ phân tích
Khu vực hiển thị ảnh (PNG) biểu đồ hoặc biểu đồ tương tác, kèm theo bảng chú thích dữ liệu (Legend Panel) chi tiết.

2.5.5. Giao diện báo cáo tự động
Khu vực hiển thị văn bản báo cáo dưới dạng đoạn văn, gạch đầu dòng, được sinh bởi AI Agent. Phía dưới có thể có hộp thoại chat để người dùng tiếp tục đặt câu hỏi truy vấn riêng lẻ về dữ liệu.

CHƯƠNG 3: KẾT LUẬN
3.1. Ưu điểm
- Giải pháp tự động hóa giúp giảm thiểu tối đa thời gian thực hiện phân tích số liệu thủ công.
- Thuật toán làm sạch dữ liệu sâu (deep_clean) giúp chuẩn hóa bộ dữ liệu thô một cách an toàn và chi tiết.
- Tính năng tự động vẽ đồ thị bằng Matplotlib hoạt động chính xác dựa trên việc nhận diện kiểu cột.
- AI Agent hỗ trợ phân tích dữ liệu trực quan, đưa ra nhận xét bằng ngôn ngữ tự nhiên, rất dễ hiểu cho người không chuyên.

3.2. Nhược điểm
- AI đôi khi có thể gặp tình trạng ảo giác (hallucination) khi đưa ra nhận định không hoàn toàn khớp với số liệu thực tế, đặc biệt đối với dữ liệu phức tạp.
- Cần có kết nối internet và có thể phát sinh chi phí khi gọi API của LLM.
- Khả năng xử lý tệp Excel có dung lượng siêu lớn (vài GB) trên giao diện web có thể gặp giới hạn về bộ nhớ và thời gian chờ (timeout).

3.3. Hướng phát triển toàn diện
- Nâng cấp mô hình AI (Fine-tuning) để Agent trả lời các thuật ngữ chuyên ngành (Tài chính, Y tế, Giáo dục) chính xác hơn.
- Cải thiện tối ưu hóa hiệu suất để xử lý dữ liệu lớn (Big Data) bằng thư viện Dask hoặc Spark.
- Bổ sung nhiều tùy chọn biểu đồ tương tác bằng Plotly.
- Hỗ trợ kết nối trực tiếp đến các cơ sở dữ liệu (MySQL, PostgreSQL, MongoDB) thay vì chỉ tải tệp Excel cục bộ.

TÀI LIỆU THAM KHẢO
[1] Wes McKinney. Python for Data Analysis, 3rd Edition. O'Reilly Media, 2022.
[2] Jake VanderPlas. Python Data Science Handbook. O'Reilly Media, 2016.
[3] Matplotlib Documentation. "Matplotlib: Visualization with Python." https://matplotlib.org
[4] Pandas Documentation. "pandas - Python Data Analysis Library." https://pandas.pydata.org
[5] OpenAI API Documentation. https://platform.openai.com/docs
