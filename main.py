import os
import sys
import webbrowser
# pyrefly: ignore [missing-import]
from flask import Flask, render_template, jsonify, request, send_file
from python_simulation.simulate_bin import BinSimulator
from reports.generator import init_csv, log_to_csv, generate_pdf_report, CSV_FILE, PDF_FILE

# Set up paths
TEMPLATE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "dashboard/templates"))
STATIC_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "dashboard/static"))

app = Flask(__name__, template_folder=TEMPLATE_DIR, static_folder=STATIC_DIR)

# Initialize simulator instance
simulator = BinSimulator(bin_id="smartbin_node_1")

# Ensure telemetry logs are initialized
init_csv()

@app.route('/')
def home():
    """Serves the dashboard home page."""
    return render_template('index.html')

@app.route('/api/data', methods=['GET'])
def get_data():
    """API endpoint to fetch the latest telemetry data."""
    # Update simulator values
    telemetry = simulator.update()
    
    # Log telemetry entry to CSV log
    log_to_csv(
        bin_id=telemetry["bin_id"],
        distance=telemetry["distance"],
        fill_percentage=telemetry["fill_percentage"],
        status=telemetry["status"],
        temp=telemetry["temp"],
        humidity=telemetry["humidity"],
        gas_level=telemetry["gas_level"],
        alert_triggered=telemetry["alert_triggered"]
    )
    
    return jsonify(telemetry)

@app.route('/api/set-mode', methods=['POST'])
def set_mode():
    """API endpoint to set the simulator mode (empty, half-full, nearly-full, full, dynamic)."""
    data = request.get_json()
    mode = data.get("mode")
    try:
        simulator.set_mode(mode)
        return jsonify({"status": "success", "mode": mode})
    except ValueError as e:
        return jsonify({"status": "error", "message": str(e)}), 400

@app.route('/download-pdf', methods=['GET'])
def download_pdf():
    """Generates the latest PDF report on-the-fly and downloads it."""
    success = generate_pdf_report()
    if success and os.path.exists(PDF_FILE):
        return send_file(PDF_FILE, as_attachment=True, download_name="Waste_Management_Report.pdf")
    else:
        return jsonify({"status": "error", "message": "Failed to generate report. Make sure logs exist."}), 500

@app.route('/download-csv', methods=['GET'])
def download_csv():
    """Downloads the raw telemetry log CSV file."""
    if os.path.exists(CSV_FILE):
        return send_file(CSV_FILE, as_attachment=True, download_name="Waste_Management_Telemetry_Logs.csv")
    else:
        return jsonify({"status": "error", "message": "No log file found."}), 404

def main():
    # Print welcome block
    print("==========================================================")
    print("   Smart Waste Management & Bin Level Simulation Server   ")
    print("==========================================================")
    print("Initializing Flask server on http://127.0.0.1:5000")
    print("Opening web dashboard in your default browser...")
    
    # Auto-open browser in a separate thread so it doesn't block Flask startup
    webbrowser.open_new_tab("http://127.0.0.1:5000")
    
    # Run Flask server
    app.run(host="127.0.0.1", port=5000, debug=False)

if __name__ == '__main__':
    main()
