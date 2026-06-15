# ── build stage ─────────────────────────────────────────────────────────
FROM python:3.12-alpine AS build
WORKDIR /app
# musl needs build toolchain only for the wheel build, not at runtime
RUN apk add --no-cache build-base libffi-dev
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ── runtime stage ───────────────────────────────────────────────────────
FROM python:3.12-alpine
WORKDIR /app
COPY --from=build /install /usr/local
COPY app ./app
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
