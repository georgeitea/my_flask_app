import os
import sys
import socket
import threading
import pyautogui
import webbrowser
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_socketio import SocketIO, emit

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, "templates"),
    static_folder=os.path.join(BASE_DIR, "static")
)
socketio = SocketIO(app, async_mode="threading")
app.secret_key = 'your_secret_key'
PORT = 5000

# --- Καθολικές μεταβλητές ---
server_running = False
server_thread = None
server_socket = None
global_client_socket = None
global_target_ip = None


def send_adb(cmd):

    os.system(f"adb shell input keyevent {cmd}")

def handle_command_locally(command):
    if command == "play_pause":
        pyautogui.press("space")
        send_adb(85)
    elif command == "volume_up":
        pyautogui.press("volumeup")
        send_adb(24)
    elif command == "volume_down":
        pyautogui.press("volumedown")
        send_adb(25)
    elif command == "repeat":
        pyautogui.press("0")
        pyautogui.press("left")
        send_adb(7)

def socket_server():
    HOST = "0.0.0.0"
    global server_socket, server_running
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        # Επιτρέπει την άμεση επαναχρησιμοποίηση της διεύθυνσης μετά το κλείσιμο
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((HOST, PORT))
        server_socket.listen(1) # Σημείωση: Ακούει για 1 σύνδεση κάθε φορά
        print(f"Ο Server ακούει στη θύρα {PORT}...")
    except socket.error as e:
        print(f"Σφάλμα δέσμευσης θύρας (server): {e}")
        server_running = False
        return

    while server_running:
        conn = None
        client_ip = None 
        try:
            conn, addr = server_socket.accept()
            client_ip = addr[0] 
            print(f"Σύνδεση από: {client_ip}")

        
            with app.app_context():
                socketio.emit('client_connected', {'ip': client_ip}, namespace='/')

            with conn:
                while server_running:
                    try:
                        data = conn.recv(1024).decode("utf-8")
                    except Exception as e:
                        print(f"Σφάλμα λήψης δεδομένων (server): {e}")
                        break # Βγαίνει από τον εσωτερικό βρόχο σε περίπτωση σφάλματος
                    if not data:
                        print(f"Ο πελάτης {client_ip} αποσυνδέθηκε.")
                        # Εκπέμπουμε και την αποσύνδεση
                        with app.app_context():
                            socketio.emit('client_disconnected', {'ip': client_ip}, namespace='/')
                        break # Βγαίνει από τον εσωτερικό βρόχο αν δεν υπάρχουν δεδομένα (ο client αποσυνδέθηκε)
                    print(f"Λάβαμε: {data}")
                    handle_command_locally(data)
        except OSError:
            # Αυτό συμβαίνει όταν καλείται το server_socket.close(), διακόπτοντας την accept() κλήση
            print("Ο διακομιστής socket έκλεισε.")
            break
        except Exception as e:
            print(f"Γενικό σφάλμα διακομιστή: {e}")
            if conn:
                conn.close() # Εξασφαλίζει ότι η σύνδεση κλείνει σε περίπτωση σφάλματος
            # Αν υπήρχε συνδεδεμένος client, εκπέμπουμε την αποσύνδεση και σε γενικό σφάλμα
            if client_ip:
                with app.app_context():
                    socketio.emit('client_disconnected', {'ip': client_ip}, namespace='/')

def client(server_ip, cmd):

    global global_client_socket, global_target_ip

    if global_client_socket is None or global_target_ip != server_ip:
      
        if global_client_socket:
            try:
                global_client_socket.shutdown(socket.SHUT_RDWR) # Κλείνει και τις δύο κατευθύνσεις
                global_client_socket.close()
                print("Κλείσιμο προηγούμενης σύνδεσης client socket.")
            except Exception as e:
                print(f"Σφάλμα κατά το κλείσιμο προηγούμενης σύνδεσης: {e}")
            finally:
                global_client_socket = None

        
        try:
            new_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            new_socket.connect((server_ip, PORT))
            new_socket.settimeout(0.5) # Θέτει ένα μικρό timeout για την recv
            global_client_socket = new_socket
            global_target_ip = server_ip
            print(f"Επιτυχής δημιουργία νέας σύνδεσης client socket στο {server_ip}:{PORT}")
        except socket.error as e:
            print(f"Σφάλμα σύνδεσης client socket στο {server_ip}:{PORT}: {e}")
            global_client_socket = None
            global_target_ip = None
            return False 

  
    if global_client_socket:
        try:
            global_client_socket.sendall(cmd.encode("utf-8"))
            print(f"Εντολή '{cmd}' στάλθηκε στον {server_ip}")
            return True # Υποδεικνύει ότι η εντολή στάλθηκε επιτυχώς
        except socket.error as e:
            print(f"Σφάλμα αποστολής εντολής ή λήψης απάντησης: {e}. Η σύνδεση μπορεί να έχει κλείσει.")
            try:
                global_client_socket.shutdown(socket.SHUT_RDWR)
                global_client_socket.close()
            except Exception:
                pass 
            global_client_socket = None
            global_target_ip = None
            return False 
    return False 

# --- Flask routes ---

@app.route('/')
def start_menu():
    return render_template('start_menu.html')
    

@app.route('/index')
def index():
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    if username == 'george' and password == '123':
        session['logged_in'] = True
        return redirect(url_for('welcome'))
    else:
        return render_template('index.html', error='Λάθος username ή password!')

@app.route('/welcome')
def welcome():

    if not session.get('logged_in'):
        return redirect(url_for('index'))
    return render_template('welcome.html')

@app.route('/server')
def server_page():

    if not session.get('logged_in'):
        return redirect(url_for('index'))
    return render_template('server.html')

@app.route('/start_server', methods=['POST'])
def start_server():

    global server_running, server_thread
    if not session.get('logged_in'):
        return redirect(url_for('index'))
    if not server_running:
        server_running = True
        server_thread = threading.Thread(target=socket_server, daemon=True)
        server_thread.start()
        return jsonify({'status': 'started'})
    else:
        return jsonify({'status': 'Server is already running!'})

@app.route('/connect')
def connect():
    """
    Ανακατευθύνει στο server_members.html.
    """
    if not session.get('logged_in'):
        return redirect(url_for('index'))
    return render_template('server_members.html')

@app.route('/server_members')
def show_clients():

    if not session.get('logged_in'):
         return redirect(url_for('index'))
    return render_template('server_members.html')

@app.route("/stop_server", methods=['POST'])
def stop_server():
    global server_running, server_socket
    if not session.get('logged_in'):
        return redirect(url_for('index'))
    if server_running:
        server_running = False
        if server_socket:
            server_socket.close() # Αυτό θα προκαλέσει OSError στην server_socket.accept()
        print("Ο server τερμάτισε από το Flask stop_server!")
        return jsonify({"status": "stopped"})
    else:
        return jsonify({"status": "Server is not running!"})

@app.route('/controller')
def client_page():
    if not session.get('logged_in'):
        return redirect(url_for('index'))
    return render_template('controller.html')

@app.route('/check_ip', methods=['POST'])
def check_ip():

  
    data_json = request.get_json()
    ip = data_json.get('ip')
    try:
        # Πρέπει να ορίσουμε το global_target_ip εδώ, ώστε η client() να γνωρίζει πού να συνδεθεί
        global global_target_ip, global_client_socket
        # Πρώτα, προσπαθούμε να συνδεθούμε για να επαληθεύσουμε ότι υπάρχει
        temp_socket = socket.create_connection((ip, PORT), timeout=2)
        temp_socket.close() # Κλείσιμο προσωρινής σύνδεσης

        global_target_ip = ip
        if global_client_socket:
            try:
                global_client_socket.shutdown(socket.SHUT_RDWR)
                global_client_socket.close()
            except Exception:
                pass
            global_client_socket = None # Επιβάλλει επανασύνδεση στην πρώτη εντολή

        session['target_ip'] = ip # Εξακολουθεί να είναι χρήσιμο για εμφάνιση στον χρήστη αν χρειάζεται
        return jsonify({'exists': True})
    except Exception as e:
        print(f"Σφάλμα ελέγχου IP: {e}")
        return jsonify({'exists': False})

@app.route('/menu_controller')
def menu_controller():
    """
    Εμφανίζει το μενού του controller.
    """
    if not session.get('logged_in'):
        return redirect(url_for('index'))
    return render_template('menu_controller.html')

@socketio.on('command')
def handle_client_command(command_data):
    command = command_data.get('command')
    target_ip = session.get('target_ip')

    if target_ip:
        print(f"Λήψη εντολής: {command} για IP: {target_ip}")
        # Καλούμε την τροποποιημένη συνάρτηση client
        success = client(target_ip, command)
        if success:
            emit('command_ack', {'status': 'success', 'command': command})
        else:
            emit('command_ack', {'status': 'failed', 'command': command, 'message': 'Αδυναμία αποστολής εντολής. Ελέγξτε τη σύνδεση.'})
    else:
        emit('command_ack', {'status': 'failed', 'command': command, 'message': 'Δεν έχει οριστεί IP προορισμού.'})

if __name__ == '__main__':
    try:
        webbrowser.open("http://127.0.0.1:8000/")
        socketio.run(app, port=8000, debug=True)
    except Exception as e:
        print("Σφάλμα:", e)
    input("Πατήστε Enter για έξοδο...")
    
