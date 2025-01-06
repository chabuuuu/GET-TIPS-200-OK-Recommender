# FROM openjdk:11-jdk-slim

# # Cài đặt conda
# RUN apt-get update && apt-get install -y wget && \
#     wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O /miniconda.sh && \
#     bash /miniconda.sh -b -p /opt/conda && \
#     rm -f /miniconda.sh && \
#     apt-get remove -y wget && apt-get autoremove -y && \
#     apt-get clean && rm -rf /var/lib/apt/lists/*


# ENV PATH=/opt/conda/bin:$PATH

# # Thiết lập thư mục làm việc
# WORKDIR /app

# # Sao chép file environment.yml vào container
# COPY environment.yml .

# # Tạo môi trường Conda và kích hoạt
# RUN conda env create -f environment.yml && conda clean -afy

# # Kích hoạt môi trường theo mặc định
# # RUN echo "conda activate $(head -1 environment.yml | cut -d' ' -f2)" > ~/.bashrc
# # ENV PATH /opt/conda/envs/$(head -1 environment.yml | cut -d' ' -f2)/bin:$PATH

# # Đảm bảo conda được kích hoạt chính xác trong Docker
# SHELL ["conda", "run", "-n", "GetTipsRec", "/bin/bash", "-c"]

# RUN conda list -n GetTipsRec


# # Sao chép toàn bộ mã nguồn vào container
# COPY . .

# # Khai báo cổng (nếu ứng dụng cần)
# EXPOSE 5000

# # Command để chạy ứng dụng
# # CMD ["python", "production.py"]

# # Thiết lập CMD để chạy script Python
# CMD ["conda", "run", "--no-capture-output", "-n", "GetTipsRec", "python", "production.py"]



# Giai đoạn 1: Cài đặt Conda và môi trường
FROM continuumio/miniconda3 AS builder
WORKDIR /env
COPY environment.yml .
RUN conda env create -f environment.yml && conda clean -afy

# Giai đoạn 2: Image cuối cùng
FROM openjdk:11-jre-slim
WORKDIR /app
COPY --from=builder /opt/conda /opt/conda
ENV PATH=/opt/conda/bin:$PATH
COPY . .
CMD ["conda", "run", "--no-capture-output", "-n", "GetTipsRec", "python", "production.py"]
