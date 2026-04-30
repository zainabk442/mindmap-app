# from flask import Flask, render_template, request
# import os
# import cv2
#
# app = Flask(__name__)
#
# UPLOAD_FOLDER = 'static/uploads'
# app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
#
# # Home page
# @app.route('/')
# def index():
#     return render_template('index.html')
#
# # Upload + process
# @app.route('/upload', methods=['POST'])
# def upload():
#     file = request.files['image']
#
#     if file:
#         filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
#         file.save(filepath)
#
#         # Example processing (just read image)
#         img = cv2.imread(filepath)
#         gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
#         cv2.imwrite(filepath, gray)
#
#         return f"Processed Image Saved: {filepath}"
#
#     return "No file uploaded"
#
# if __name__ == '__main__':
#     app.run(host='0.0.0.0', port=5000)



from flask import Flask, render_template, request
import os
import cv2

app = Flask(__name__)

UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Home page
@app.route('/')
def index():
    return render_template('index.html')


# Upload + process
@app.route('/upload', methods=['POST'])
def upload():
    file = request.files['image']

    if file:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filepath)

        # Process image (convert to grayscale)
        img = cv2.imread(filepath)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        cv2.imwrite(filepath, gray)

        # Send image back to UI
        return render_template('index.html', image=filepath)

    return "No file uploaded"


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)