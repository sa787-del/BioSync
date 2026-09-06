"""Runtime for the supplied BioSync Diabetes hybrid-QML artifact.

The artifact contains trained quantum weights, a classical head and scaling
metadata, but not the original training source. The runtime therefore reconstructs
the documented circuit path and explicitly marks that provenance.
"""
from pathlib import Path
import numpy as np
import joblib
import torch

ROOT = Path(__file__).resolve().parent
MODEL_DIR = ROOT / "models" / "diabetes"
FEATURES = ["gender", "age", "hypertension", "heart_disease", "smoking_history", "bmi", "HbA1c_level", "blood_glucose_level"]
Q_FEATURES = ["age", "bmi", "HbA1c_level", "blood_glucose_level"]
SCALER = joblib.load(MODEL_DIR / "scaler.pkl")
Q_SCALER = joblib.load(MODEL_DIR / "quantum_scaler.pkl")
ARTIFACT = torch.load(MODEL_DIR / "finetuned_hybrid_qml.pt", map_location="cpu", weights_only=False)
STATE = ARTIFACT["model_state_dict"]
Q_WEIGHTS = STATE["quantum_layer.weights"].detach().cpu()
HEAD_W1 = STATE["classical_head.0.weight"].detach().cpu()
HEAD_B1 = STATE["classical_head.0.bias"].detach().cpu()
HEAD_W2 = STATE["classical_head.3.weight"].detach().cpu()
HEAD_B2 = STATE["classical_head.3.bias"].detach().cpu()
N_QUBITS = int(ARTIFACT.get("n_qubits", 4))
N_LAYERS = int(ARTIFACT.get("n_layers", 3))
THRESHOLD = float(ARTIFACT.get("decision_threshold", 0.53))

def encode_inputs(features: dict) -> np.ndarray:
    numeric = np.array([[float(features[k]) for k in Q_FEATURES]], dtype=float)
    return Q_SCALER.transform(SCALER.transform(numeric)).astype(np.float64)

def _classical_head(q_features: np.ndarray):
    q = np.asarray(q_features, dtype=np.float64).reshape(-1)
    hidden = np.maximum(0.0, HEAD_W1.numpy().astype(np.float64) @ q + HEAD_B1.numpy().astype(np.float64))
    logit = float((HEAD_W2.numpy().astype(np.float64) @ hidden + HEAD_B2.numpy().astype(np.float64)).reshape(-1)[0])
    probability = float(1.0 / (1.0 + np.exp(-np.clip(logit, -60.0, 60.0))))
    return logit, probability

def _predict_with_pennylane(x: np.ndarray) -> np.ndarray:
    import pennylane as qml
    dev = qml.device("default.qubit", wires=N_QUBITS)
    @qml.qnode(dev)
    def circuit(inputs, weights):
        qml.AngleEmbedding(inputs, wires=range(N_QUBITS), rotation="Y")
        for layer in range(N_LAYERS):
            for wire in range(N_QUBITS):
                qml.RY(float(weights[layer, wire, 0]), wires=wire)
                qml.RZ(float(weights[layer, wire, 1]), wires=wire)
            for wire in range(N_QUBITS - 1):
                qml.CNOT(wires=[wire, wire + 1])
        return [qml.expval(qml.PauliZ(w)) for w in range(N_QUBITS)]
    return np.asarray(circuit(np.asarray(x, dtype=np.float64), Q_WEIGHTS.numpy().astype(np.float64)), dtype=np.float64)

def _ry(theta):
    c, s = np.cos(theta / 2.0), np.sin(theta / 2.0)
    return np.array([[c, -s], [s, c]], dtype=np.complex128)

def _rz(theta):
    return np.array([[np.exp(-1j * theta / 2.0), 0], [0, np.exp(1j * theta / 2.0)]], dtype=np.complex128)

def _apply_single_qubit(state, gate, wire):
    tensor = state.reshape((2,) * N_QUBITS)
    tensor = np.moveaxis(tensor, wire, 0).reshape(2, -1)
    tensor = gate @ tensor
    tensor = np.moveaxis(tensor.reshape((2,) + (2,) * (N_QUBITS - 1)), 0, wire)
    return tensor.reshape(-1)

def _apply_cnot(state, control, target):
    out = np.zeros_like(state)
    for idx, amp in enumerate(state):
        bits = [(idx >> (N_QUBITS - 1 - k)) & 1 for k in range(N_QUBITS)]
        if bits[control]: bits[target] ^= 1
        j = 0
        for bit in bits: j = (j << 1) | bit
        out[j] = amp
    return out

def _predict_with_numpy_simulator(x):
    state = np.zeros(2 ** N_QUBITS, dtype=np.complex128); state[0] = 1.0 + 0.0j
    for wire, angle in enumerate(x): state = _apply_single_qubit(state, _ry(float(angle)), wire)
    weights = Q_WEIGHTS.numpy().astype(np.float64)
    for layer in range(N_LAYERS):
        for wire in range(N_QUBITS):
            state = _apply_single_qubit(state, _ry(float(weights[layer, wire, 0])), wire)
            state = _apply_single_qubit(state, _rz(float(weights[layer, wire, 1])), wire)
        for wire in range(N_QUBITS - 1): state = _apply_cnot(state, wire, wire + 1)
    probabilities = np.abs(state) ** 2; expectations = []
    for wire in range(N_QUBITS):
        value = sum((1.0 if ((idx >> (N_QUBITS - 1 - wire)) & 1) == 0 else -1.0) * p for idx, p in enumerate(probabilities))
        expectations.append(float(np.real(value)))
    return np.asarray(expectations, dtype=np.float64)

def _quantum_features(x):
    try: return _predict_with_pennylane(x), "PennyLane default.qubit simulator"
    except Exception as exc:
        try: return _predict_with_numpy_simulator(x), "Local 4-qubit statevector simulator"
        except Exception as fallback_exc: raise RuntimeError(f"Diabetes hybrid QML execution failed: {type(exc).__name__}; {type(fallback_exc).__name__}") from fallback_exc

def predict(features: dict):
    x = encode_inputs(features)[0]
    q_features, execution_backend = _quantum_features(x)
    logit, probability = _classical_head(q_features)
    return {"model":"FinetunedHybridQML","prediction":int(probability >= THRESHOLD),"probability":probability,"decision_score":logit,"decision_threshold":THRESHOLD,"feature_order":FEATURES,"quantum_features":Q_FEATURES,"execution_backend":execution_backend,"details":{"type":"Hybrid quantum-classical neural model","verification_status":"Executable artifact reconstruction; original training source was not bundled.","configuration":{"n_qubits":N_QUBITS,"n_layers":N_LAYERS,"qml_parameters":int(N_LAYERS*N_QUBITS*2),"decision_threshold":THRESHOLD}}}
