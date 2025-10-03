from flask import Flask, jsonify

app = Flask(__name__)

@app.route("/")
def root():
    return "Welcome to Needle!"

@app.route("/health")
def health_check():
    status = {"status": "healthy"}
    http_status_code = 200

    #db connection checks when added

    return jsonify(status), http_status_code

if __name__ == "__main__":
    app.run(debug=True)
