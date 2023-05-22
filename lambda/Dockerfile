# Define global ARGs used across stages
ARG FUNCTION_DIR="/function"
ARG RUNTIME_VERSION="3.8"
ARG DISTRO_VERSION="3.13"

# Stage 1 - bundle base image + runtime
# Grab a fresh copy of the image and install GCC
FROM python:${RUNTIME_VERSION}-alpine${DISTRO_VERSION} AS python-alpine
RUN apk add --no-cache \
    libstdc++

# Stage 2 - build function and dependencies
FROM python-alpine AS build-image
# Install GCC
RUN apk add --no-cache \
    build-base \
    libtool \
    cmake

# Include global ARGs we've defined above
ARG FUNCTION_DIR
ARG RUNTIME_VERSION
# Create function directory
RUN mkdir -p ${FUNCTION_DIR}

# Install the function's dependencies using file requirements.txt
# from your project directory.
COPY ./requirements.txt /
RUN  pip install --target ${FUNCTION_DIR} -r /requirements.txt

# Stage 3 - final runtime image
# Grab a fresh copy of the Python image
# and copy over the Lambda function and dependencies
FROM python-alpine
# Include global arg in this stage of the build
ARG FUNCTION_DIR
# Set working directory to function root directory
WORKDIR ${FUNCTION_DIR}
# Copy handler function and package from build-image to runtime-image
COPY --from=build-image ${FUNCTION_DIR} ${FUNCTION_DIR}
COPY ./lambda_function.py ${FUNCTION_DIR}
CMD [ "/usr/local/bin/python3", "${FUNCTION_DIR}/lambda_function.py" ]

