import { useState, useRef } from "react";
import "./App.css";

const API_URL = "http://127.0.0.1:8000";
const TARGET_SAMPLE_RATE = 16000;

const initialForm = {
  recipient: "Rahul",
  amount: "500",
  typicalAmount: "1000",
  recipientKnown: true,
  recipientMatch: "0.95",
  voiceConfidence: "0.95",
};

// Convert recorded audio into mono, 16 kHz PCM WAV.
async function convertToWav(audioBlob) {
  const AudioContextClass =
    window.AudioContext || window.webkitAudioContext;

  if (!AudioContextClass) {
    throw new Error("Audio processing is not supported.");
  }

  const audioContext = new AudioContextClass();

  try {
    const arrayBuffer = await audioBlob.arrayBuffer();
    const decodedBuffer =
      await audioContext.decodeAudioData(arrayBuffer);

    const offlineContext = new OfflineAudioContext(
      1,
      Math.ceil(decodedBuffer.duration * TARGET_SAMPLE_RATE),
      TARGET_SAMPLE_RATE
    );

    const source = offlineContext.createBufferSource();
    source.buffer = decodedBuffer;
    source.connect(offlineContext.destination);
    source.start(0);

    const renderedBuffer =
      await offlineContext.startRendering();

    const samples = renderedBuffer.getChannelData(0);
    const dataSize = samples.length * 2;

    const wavBuffer = new ArrayBuffer(44 + dataSize);
    const view = new DataView(wavBuffer);

    function writeString(offset, string) {
      for (let i = 0; i < string.length; i++) {
        view.setUint8(offset + i, string.charCodeAt(i));
      }
    }

    writeString(0, "RIFF");
    view.setUint32(4, 36 + dataSize, true);
    writeString(8, "WAVE");
    writeString(12, "fmt ");
    view.setUint32(16, 16, true);
    view.setUint16(20, 1, true);
    view.setUint16(22, 1, true);
    view.setUint32(24, TARGET_SAMPLE_RATE, true);
    view.setUint32(28, TARGET_SAMPLE_RATE * 2, true);
    view.setUint16(32, 2, true);
    view.setUint16(34, 16, true);
    writeString(36, "data");
    view.setUint32(40, dataSize, true);

    let offset = 44;

    for (let i = 0; i < samples.length; i++) {
      const sample = Math.max(-1, Math.min(1, samples[i]));

      view.setInt16(
        offset,
        sample < 0 ? sample * 32768 : sample * 32767,
        true
      );

      offset += 2;
    }

    return new Blob([wavBuffer], { type: "audio/wav" });
  } finally {
    await audioContext.close();
  }
}

// Convert spoken number words into a numeric amount.
function parseSpokenNumber(text) {
  const words = text
    .toLowerCase()
    .replace(/-/g, " ")
    .split(/\s+/);

  const numbers = {
    zero: 0,
    one: 1,
    two: 2,
    three: 3,
    four: 4,
    five: 5,
    six: 6,
    seven: 7,
    eight: 8,
    nine: 9,
    ten: 10,
    eleven: 11,
    twelve: 12,
    thirteen: 13,
    fourteen: 14,
    fifteen: 15,
    sixteen: 16,
    seventeen: 17,
    eighteen: 18,
    nineteen: 19,
    twenty: 20,
    thirty: 30,
    forty: 40,
    fifty: 50,
    sixty: 60,
    seventy: 70,
    eighty: 80,
    ninety: 90,
  };

  let total = 0;
  let current = 0;
  let found = false;

  for (const word of words) {
    if (numbers[word] !== undefined) {
      current += numbers[word];
      found = true;
    } else if (word === "hundred") {
      current = (current || 1) * 100;
      found = true;
    } else if (
      word === "thousand" ||
      word === "thousands"
    ) {
      total += (current || 1) * 1000;
      current = 0;
      found = true;
    } else if (
      word === "lakh" ||
      word === "lakhs" ||
      word === "lac"
    ) {
      total += (current || 1) * 100000;
      current = 0;
      found = true;
    } else if (
      word === "crore" ||
      word === "crores"
    ) {
      total += (current || 1) * 10000000;
      current = 0;
      found = true;
    }
  }

  return found ? total + current : null;
}

// Extract payment details without assuming a named recipient is trusted.
function extractPaymentDetails(text) {
  const normalized = text
    .toLowerCase()
    .replace(/,/g, "")
    .replace(/\s+/g, " ")
    .trim();

  let amount = null;

  // First: numeric currency amounts.
  const numericPatterns = [
    /(?:₹|rs\.?|rupees?)\s*(\d+(?:\.\d+)?)/i,
    /(\d+(?:\.\d+)?)\s*(?:rupees?|rs\.?)/i,
    /\b(?:send|pay|transfer)\s+(?:₹|rs\.?)?\s*(\d+(?:\.\d+)?)/i,
  ];

  for (const pattern of numericPatterns) {
    const match = normalized.match(pattern);

    if (match) {
      amount = match[1];
      break;
    }
  }

  // Second: spoken currency amounts.
  if (!amount) {
    const spokenMatch = normalized.match(
      /\b(?:send|pay|transfer)\s+(.+?)\s+(?:rupees?|rs\.?)\b/i
    );

    if (spokenMatch) {
      const parsed = parseSpokenNumber(spokenMatch[1]);

      if (parsed !== null && parsed > 0) {
        amount = String(parsed);
      }
    }
  }

  // Also support amounts like "two lakh" before "to Rahul".
  if (!amount) {
    const spokenMatch = normalized.match(
      /\b(?:send|pay|transfer)\s+(.+?)\s+to\b/i
    );

    if (spokenMatch) {
      const parsed = parseSpokenNumber(spokenMatch[1]);

      if (parsed !== null && parsed > 0) {
        amount = String(parsed);
      }
    }
  }

  // Detect explicitly unknown or new recipients.
  const unknownRecipient = /\b(?:(?:an?|the)\s+)?(?:unknown|new|untrusted|first[- ]time)\s+(?:recipient|payee|contact|person)\b/i.test(
    normalized
  );

  if (unknownRecipient) {
    return {
      amount,
      recipient: "Unknown recipient",
      recipientKnown: false,
      recipientMatch: "0.20",
      unknownRecipient: true,
    };
  }

  // Extract a named recipient after "to".
  const recipientMatch = normalized.match(
    /\bto\s+(?:an?\s+|the\s+)?([a-z][a-z'-]*(?:\s+[a-z][a-z'-]*){0,3})(?=\s+(?:for|of|rupees?|rs\.?|and|using)\b|[,.!?]|$)/i
  );

  const recipient = recipientMatch
    ? recipientMatch[1].trim()
    : null;

  return {
    amount,
    recipient,
    recipientKnown: null,
    recipientMatch: null,
    unknownRecipient: false,
  };
}

function App() {
  const [form, setForm] = useState(initialForm);

  const [features, setFeatures] = useState(
    Array(23).fill("0").join(", ")
  );

  const [result, setResult] = useState(null);
  const [voiceResult, setVoiceResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const [transcript, setTranscript] = useState(
    "Send 500 rupees to Rahul"
  );

  const [isRecording, setIsRecording] = useState(false);
  const [voiceLoading, setVoiceLoading] = useState(false);
  const [voiceStatus, setVoiceStatus] = useState("");
  const [voiceError, setVoiceError] = useState("");

  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const streamRef = useRef(null);

  const update = (key, value) => {
    setForm((prev) => ({ ...prev, [key]: value }));
    setResult(null);
    setVoiceResult(null);
    setVoiceStatus("");
    setVoiceError("");
  };

  async function startRecording() {
    try {
      setVoiceError("");
      setVoiceStatus("");
      setError("");

      if (!navigator.mediaDevices?.getUserMedia) {
        throw new Error(
          "Microphone access requires localhost or HTTPS."
        );
      }

      if (!window.MediaRecorder) {
        throw new Error(
          "Audio recording is not supported by this browser."
        );
      }

      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          channelCount: 1,
          echoCancellation: true,
          noiseSuppression: true,
        },
      });

      streamRef.current = stream;
      audioChunksRef.current = [];

      const supportedTypes = [
        "audio/webm;codecs=opus",
        "audio/webm",
        "audio/mp4",
      ];

      const mimeType = supportedTypes.find((type) =>
        MediaRecorder.isTypeSupported(type)
      );

      const recorder = mimeType
        ? new MediaRecorder(stream, { mimeType })
        : new MediaRecorder(stream);

      mediaRecorderRef.current = recorder;

      recorder.ondataavailable = (event) => {
        if (event.data && event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      recorder.onerror = () => {
        setVoiceError(
          "An error occurred during audio recording."
        );
        setIsRecording(false);
        setVoiceLoading(false);

        stream.getTracks().forEach((track) => track.stop());
        streamRef.current = null;
      };

      recorder.onstop = async () => {
        stream.getTracks().forEach((track) => track.stop());
        streamRef.current = null;

        const audioBlob = new Blob(audioChunksRef.current, {
          type: recorder.mimeType || "audio/webm",
        });

        if (!audioBlob.size) {
          setVoiceError(
            "No audio was recorded. Please try again."
          );
          setVoiceLoading(false);
          return;
        }

        await transcribeRecording(audioBlob);
      };

      recorder.start();

      setIsRecording(true);
      setResult(null);
      setVoiceStatus("Listening... Speak your payment command.");
    } catch (err) {
      setVoiceError(
        err.message || "Unable to access the microphone."
      );
      setVoiceStatus("");
    }
  }

  function stopRecording() {
    const recorder = mediaRecorderRef.current;

    if (recorder && recorder.state === "recording") {
      setIsRecording(false);
      setVoiceLoading(true);
      setVoiceStatus("Processing your voice...");
      recorder.stop();
    }
  }

  async function transcribeRecording(audioBlob) {
    try {
      setVoiceError("");
      setVoiceStatus("Converting audio to WAV...");

      const wavBlob = await convertToWav(audioBlob);

      if (wavBlob.size > 10 * 1024 * 1024) {
        throw new Error(
          "Recording is too large. Keep it under 10 MB."
        );
      }

      const formData = new FormData();
      formData.append("file", wavBlob, "recording.wav");

      setVoiceStatus("Sending audio to Whisper Tiny...");

      const response = await fetch(`${API_URL}/voice-payment`, {
        method: "POST",
        body: formData,
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail || "Transcription failed."
        );
      }

      if (!data.transcript) {
        throw new Error("No speech could be recognized.");
      }

      setTranscript(data.transcript);
      setVoiceResult(data);
      setResult(null);
      setError("");

      if (data.status === "CLARIFICATION_REQUIRED") {
        setVoiceStatus(
          `Clarification required: ${data.reason}`
        );
        return;
      }

      if (data.status === "VERIFICATION_REQUIRED") {
        setVoiceStatus(
          `Recipient verification required: ${data.reason}`
        );
        return;
      }

      if (data.status === "ASSESSMENT_COMPLETED") {
        setResult(data.assessment);
        setVoiceStatus(
          "Voice assessment completed. Review the risk decision below."
        );
        return;
      }

      throw new Error("Unexpected response from the voice payment service.");

    } catch (err) {
      setVoiceError(
        err.message || "Unable to transcribe the recording."
      );
      setVoiceStatus("");
    } finally {
      setVoiceLoading(false);
    }
  }

  async function assessPayment(event) {
    event.preventDefault();

    setLoading(true);
    setError("");
    setResult(null);

    try {
      const featureValues = features
        .split(",")
        .map((value) => Number(value.trim()));

      if (
        featureValues.length !== 23 ||
        featureValues.some(
          (value) => !Number.isFinite(value)
        )
      ) {
        throw new Error(
          "Enter exactly 23 valid numeric transaction features."
        );
      }

      if (
        !Number.isFinite(Number(form.amount)) ||
        Number(form.amount) <= 0
      ) {
        throw new Error("Enter a valid payment amount.");
      }

      if (
        !Number.isFinite(Number(form.typicalAmount)) ||
        Number(form.typicalAmount) <= 0
      ) {
        throw new Error(
          "Enter a valid typical payment amount."
        );
      }

      const response = await fetch(
        `${API_URL}/predict-context`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            transaction_features: featureValues,
            context: {
              recipient_is_known: form.recipientKnown,
              amount: Number(form.amount),
              typical_amount: Number(form.typicalAmount),
              recipient_match_confidence: Number(
                form.recipientMatch
              ),
              voice_intent_confidence: Number(
                form.voiceConfidence
              ),
            },
          }),
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail || "Risk assessment failed."
        );
      }

      setResult(data);
    } catch (err) {
      setError(
        err.message.includes("fetch")
          ? "Cannot connect to the backend. Ensure FastAPI is running on port 8000."
          : err.message
      );
    } finally {
      setLoading(false);
    }
  }

  const risk = result?.risk_level?.toUpperCase() || "";
  const riskClass = risk.toLowerCase();

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <a className="brand" href="#home">
          <span className="brand-icon">V</span>
          <span>
            VeriPay
            <small>SECURE PAYMENTS</small>
          </span>
        </a>

        <div className="side-label">WORKSPACE</div>

        <a className="nav-item active" href="#home">
          ◈ &nbsp; Dashboard
        </a>

        <a className="nav-item" href="#payment">
          ↗ &nbsp; New assessment
        </a>

        <a className="nav-item" href="#security">
          ◇ &nbsp; Security overview
        </a>

        <div className="sidebar-bottom">
          <div className="security-icon">♧</div>
          <strong>Safety first</strong>
          <p>Every payment deserves a second look.</p>
          <span className="offline-tag">
            DEMO MODE · NO MONEY MOVES
          </span>
        </div>
      </aside>

      <main className="main-content" id="home">
        <header className="topbar">
          <div className="breadcrumb">
            Workspace <span>/</span> Dashboard
          </div>

          <div className="system-status">
            <i /> Risk API · Local
          </div>
        </header>

        <section className="welcome">
          <div>
            <div className="eyebrow">
              CONTEXT-AWARE PAYMENT SECURITY
            </div>
            <h1>Verify before you pay.</h1>
            <p>
              Understand payment risk before making a decision.
            </p>
          </div>

          <div className="shield-art" aria-hidden="true">
            <div className="shield">✓</div>
            <span>SECURITY LAYER</span>
          </div>
        </section>

        <section className="stat-grid" id="security">
          <article className="stat-card">
            <span className="stat-label">DECISION ENGINE</span>
            <strong>CPDE</strong>
            <small>Context-aware risk evaluation</small>
          </article>

          <article className="stat-card">
            <span className="stat-label">RISK SIGNALS</span>
            <strong>05</strong>
            <small>Recipient, amount, voice & more</small>
          </article>

          <article className="stat-card">
            <span className="stat-label">
              PAYMENT EXECUTION
            </span>
            <strong className="safe-text">Disabled</strong>
            <small>Assessment only · No real transfers</small>
          </article>
        </section>

        <div className="section-heading" id="payment">
          <div>
            <div className="eyebrow">NEW ASSESSMENT</div>
            <h2>Payment risk check</h2>
            <p>
              Review the details and evaluate the risk signals.
            </p>
          </div>

          <span className="demo-badge">
            ● &nbsp; PROTOTYPE
          </span>
        </div>

        <div className="workspace-grid">
          <section className="panel">
            <div className="panel-heading">
              <span className="panel-icon">↗</span>

              <div>
                <h3>Payment details</h3>
                <p>
                  Enter the proposed payment information.
                </p>
              </div>
            </div>

            <form onSubmit={assessPayment}>
              <label>Voice command transcript</label>

              <textarea
                rows="2"
                value={transcript}
                onChange={(e) => {
                  setTranscript(e.target.value);
                  setResult(null);
                }}
                placeholder="Example: Send 500 rupees to Rahul"
              />

              <div className="voice-controls">
                {!isRecording ? (
                  <button
                    type="button"
                    className="voice-button"
                    onClick={startRecording}
                    disabled={voiceLoading}
                  >
                    🎙 Start recording
                  </button>
                ) : (
                  <button
                    type="button"
                    className="voice-button recording"
                    onClick={stopRecording}
                  >
                    ■ Stop recording
                  </button>
                )}

                {voiceLoading && (
                  <span className="voice-status">
                    Processing audio...
                  </span>
                )}

                {isRecording && (
                  <span className="voice-status recording">
                    ● Recording
                  </span>
                )}
              </div>

              {voiceStatus && (
                <p className="voice-note">{voiceStatus}</p>
              )}
              {voiceResult && (
                <div className="voice-note">
                  <strong>Voice pipeline status:</strong>{" "}
                  {voiceResult.status}

                  {voiceResult.intent?.recipient_name && (
                    <p>
                      Recipient detected: {voiceResult.intent.recipient_name}
                    </p>
                  )}

                  {voiceResult.intent?.amount != null && (
                    <p>
                      Amount detected: ₹{voiceResult.intent.amount}
                    </p>
                  )}

                  {voiceResult.reason && <p>{voiceResult.reason}</p>}
                </div>
              )}

              {voiceError && (
                <p className="voice-error">{voiceError}</p>
              )}

              <p className="field-note">
                Speak your payment command. Review the transcript
                and extracted details before running the risk
                assessment.
              </p>

              <div className="form-row">
                <div>
                  <label>Recipient</label>
                  <input
                    value={form.recipient}
                    onChange={(e) =>
                      update("recipient", e.target.value)
                    }
                    required
                  />
                </div>

                <div>
                  <label>Amount (INR)</label>
                  <input
                    type="number"
                    min="0"
                    step="0.01"
                    value={form.amount}
                    onChange={(e) =>
                      update("amount", e.target.value)
                    }
                    required
                  />
                </div>
              </div>

              <label>Typical payment amount (INR)</label>

              <input
                type="number"
                min="0"
                step="0.01"
                value={form.typicalAmount}
                onChange={(e) =>
                  update("typicalAmount", e.target.value)
                }
                required
              />

              <label className="toggle-row">
                <span>
                  <strong>Known recipient</strong>
                  <small>
                    Is this recipient in your trusted contacts?
                  </small>
                </span>

                <input
                  type="checkbox"
                  checked={form.recipientKnown}
                  onChange={(e) =>
                    update("recipientKnown", e.target.checked)
                  }
                />
              </label>

              <div className="form-row">
                <div>
                  <label>Recipient match confidence</label>
                  <input
                    type="number"
                    min="0"
                    max="1"
                    step="0.01"
                    value={form.recipientMatch}
                    onChange={(e) =>
                      update("recipientMatch", e.target.value)
                    }
                    required
                  />
                </div>

                <div>
                  <label>Voice intent confidence</label>
                  <input
                    type="number"
                    min="0"
                    max="1"
                    step="0.01"
                    value={form.voiceConfidence}
                    onChange={(e) =>
                      update("voiceConfidence", e.target.value)
                    }
                    required
                  />
                </div>
              </div>

              <details className="advanced">
                <summary>
                  Advanced · Transaction model inputs
                </summary>

                <p>
                  Enter exactly 23 comma-separated numeric
                  features for the fraud model.
                </p>

                <textarea
                  rows="3"
                  value={features}
                  onChange={(e) => setFeatures(e.target.value)}
                />

                <small>
                  Currently initialized with zeros for a smoke
                  test. Replace with correctly mapped features
                  for meaningful model predictions.
                </small>
              </details>

              {error && (
                <div className="error-message">{error}</div>
              )}

              <button
                className="primary-button"
                type="submit"
                disabled={
                  loading ||
                  isRecording ||
                  voiceLoading ||
                  voiceResult?.status === "CLARIFICATION_REQUIRED" ||
                  voiceResult?.status === "VERIFICATION_REQUIRED"
                }
              >
                {loading
                  ? "Assessing risk…"
                  : "Evaluate payment risk →"}
              </button>

              <p className="disclaimer">
                This prototype evaluates risk only. It does not
                initiate or authorize a UPI payment.
              </p>
            </form>
          </section>

          <section className="panel results-panel">
            <div className="panel-heading">
              <span className="panel-icon">◎</span>

              <div>
                <h3>Risk assessment</h3>
                <p>
                  Results from the backend decision engine.
                </p>
              </div>
            </div>

            {!result && !loading && (
              <div className="empty-state">
                <div className="empty-art">⌁</div>

                {voiceResult?.status === "CLARIFICATION_REQUIRED" ||
                  voiceResult?.status === "VERIFICATION_REQUIRED" ? (
                  <>
                    <h3>Payment assessment paused</h3>

                    <p>
                      {voiceResult.status === "CLARIFICATION_REQUIRED"
                        ? "Payment details are incomplete or the recipient could not be identified. Please correct the details or record your command again."
                        : "The recipient requires verification before a risk assessment can proceed."}
                    </p>

                    <div className="empty-checks">
                      <span>✓ Payment not executed</span>
                      <span>✓ Risk assessment paused</span>
                      <span>✓ User clarification required</span>
                    </div>
                  </>
                ) : (
                  <>
                    <h3>Ready when you are</h3>

                    <p>
                      Complete the payment details and run an
                      assessment to see the risk signals and
                      recommended action.
                    </p>

                    <div className="empty-checks">
                      <span>✓ Recipient context</span>
                      <span>✓ Transaction risk model</span>
                      <span>✓ Confirmation safeguards</span>
                    </div>
                  </>
                )}
              </div>
            )}

            {loading && (
              <div className="loading-state">
                Evaluating risk signals…
              </div>
            )}

            {result && (
              <div className="result-content">
                <div className={`risk-banner ${riskClass}`}>
                  <span className="risk-symbol">
                    {risk === "HIGH"
                      ? "!"
                      : risk === "MEDIUM"
                        ? "◇"
                        : "✓"}
                  </span>

                  <div>
                    <span className="stat-label">
                      ASSESSED RISK
                    </span>

                    <h2>{risk || "UNKNOWN"} RISK</h2>

                    <p>
                      {result.reason ||
                        "Review the decision details below."}
                    </p>
                  </div>
                </div>

                <div className="metric-grid">
                  <div className="metric">
                    <span>Fraud probability</span>
                    <strong>
                      <strong>
                        {result.fraud_probability == null
                          ? "N/A – Model not evaluated"
                          : `${(Number(result.fraud_probability) * 100).toFixed(2)}%`}
                      </strong>
                    </strong>
                  </div>

                  <div className="metric">
                    <span>Context risk score</span>
                    <strong>
                      {(
                        Number(result.context_score) * 100
                      ).toFixed(1)}%
                    </strong>
                  </div>
                </div>

                <h4>Context signals</h4>

                <div className="signal-list">
                  {Object.entries(
                    result.context_signals || {}
                  ).map(([key, value]) => (
                    <div className="signal-row" key={key}>
                      <span>
                        {key.replaceAll("_", " ")}
                      </span>

                      <strong>
                        {Number(value).toFixed(2)}
                      </strong>
                    </div>
                  ))}
                </div>

                <div className="decision-box">
                  <span>RECOMMENDED ACTION</span>

                  <strong>
                    {result.risk_decision ||
                      result.decision ||
                      "REVIEW"}
                  </strong>

                  <p>
                    {result.payment_decision ||
                      "AWAITING_REVIEW"}
                  </p>
                </div>

                <div className="execution-note">
                  <span>✓</span>
                  Payment execution:{" "}
                  <strong>
                    {result.payment_execution ||
                      "NOT_EXECUTED"}
                  </strong>
                </div>

                {result.confirmation_required && (
                  <p className="confirmation-note">
                    Explicit confirmation is required before any
                    future payment workflow could proceed.
                  </p>
                )}
              </div>
            )}
          </section>
        </div>

        <footer>
          <span>VeriPay · CPDE Research Prototype</span>

          <span>
            Risk assessment only · No live payment integration
          </span>
        </footer>
      </main>
    </div>
  );
}

export default App;
