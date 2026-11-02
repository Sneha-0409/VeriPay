
// import { useState, useRef, useEffect } from "react";
// import "./App.css";

// const API_URL = "http://127.0.0.1:8000";
// const TARGET_SAMPLE_RATE = 16000;

// const initialForm = {
//   recipient: "Rahul",
//   amount: "500",
//   typicalAmount: "1000",
//   recipientKnown: true,
//   recipientMatch: "0.95",
//   voiceConfidence: "0.95",
// };

// function parseSpokenNumber(text) {
//   const words = text.toLowerCase().replace(/-/g, " ").split(/\s+/);
//   const numbers = {
//     zero: 0, one: 1, two: 2, three: 3, four: 4, five: 5,
//     six: 6, seven: 7, eight: 8, nine: 9, ten: 10,
//     eleven: 11, twelve: 12, thirteen: 13, fourteen: 14,
//     fifteen: 15, sixteen: 16, seventeen: 17, eighteen: 18,
//     nineteen: 19, twenty: 20, thirty: 30, forty: 40,
//     fifty: 50, sixty: 60, seventy: 70, eighty: 80, ninety: 90,
//   };

//   let total = 0;
//   let current = 0;
//   let found = false;

//   for (const word of words) {
//     if (numbers[word] !== undefined) {
//       current += numbers[word];
//       found = true;
//     } else if (word === "hundred") {
//       current = (current || 1) * 100;
//       found = true;
//     } else if (["thousand", "thousands"].includes(word)) {
//       total += (current || 1) * 1000;
//       current = 0;
//       found = true;
//     } else if (["lakh", "lakhs", "lac"].includes(word)) {
//       total += (current || 1) * 100000;
//       current = 0;
//       found = true;
//     } else if (["crore", "crores"].includes(word)) {
//       total += (current || 1) * 10000000;
//       current = 0;
//       found = true;
//     }
//   }

//   return found ? total + current : null;
// }

// function extractPaymentDetails(text) {
//   const normalized = text.toLowerCase().replace(/,/g, "").replace(/\s+/g, " ").trim();

//   let amount = null;

//   const patterns = [
//     /(?:₹|rs\.?|rupees?)\s*(\d+(?:\.\d+)?)/i,
//     /(\d+(?:\.\d+)?)\s*(?:rupees?|rs\.?)/i,
//     /\b(?:send|pay|transfer)\s+(?:₹|rs\.?)?\s*(\d+(?:\.\d+)?)/i,
//   ];

//   for (const pattern of patterns) {
//     const match = normalized.match(pattern);
//     if (match) {
//       amount = match[1];
//       break;
//     }
//   }

//   if (!amount) {
//     const spokenMatch = normalized.match(
//       /\b(?:send|pay|transfer)\s+(.+?)\s+(?:rupees?|rs\.?)\b/i
//     );
//     if (spokenMatch) {
//       const parsed = parseSpokenNumber(spokenMatch[1]);
//       if (parsed !== null && parsed > 0) amount = String(parsed);
//     }
//   }

//   if (!amount) {
//     const spokenMatch = normalized.match(
//       /\b(?:send|pay|transfer)\s+(.+?)\s+to\b/i
//     );
//     if (spokenMatch) {
//       const parsed = parseSpokenNumber(spokenMatch[1]);
//       if (parsed !== null && parsed > 0) amount = String(parsed);
//     }
//   }

//   const unknownRecipient =
//     /\b(?:(?:an?|the)\s+)?(?:unknown|new|untrusted|first[- ]time)\s+(?:recipient|payee|contact|person)\b/i.test(normalized);

//   if (unknownRecipient) {
//     return {
//       amount,
//       recipient: "Unknown recipient",
//       recipientKnown: false,
//       recipientMatch: "0.20",
//       unknownRecipient: true,
//     };
//   }

//   const recipientMatch = normalized.match(
//     /\bto\s+(?:an?\s+|the\s+)?([a-z][a-z'-]*(?:\s+[a-z][a-z'-]*){0,3})(?=\s+(?:for|of|rupees?|rs\.?|and|using)\b|[,.!?]|$)/i
//   );

//   return {
//     amount,
//     recipient: recipientMatch ? recipientMatch[1].trim() : null,
//     unknownRecipient: false,
//   };
// }

// async function convertToWav(audioBlob) {
//   const AudioContextClass = window.AudioContext || window.webkitAudioContext;

//   if (!AudioContextClass) {
//     throw new Error("Audio processing is not supported.");
//   }

//   const audioContext = new AudioContextClass();

//   try {
//     const arrayBuffer = await audioBlob.arrayBuffer();
//     const decodedBuffer = await audioContext.decodeAudioData(arrayBuffer);

//     const offlineContext = new OfflineAudioContext(
//       1,
//       Math.ceil(decodedBuffer.duration * TARGET_SAMPLE_RATE),
//       TARGET_SAMPLE_RATE
//     );

//     const source = offlineContext.createBufferSource();
//     source.buffer = decodedBuffer;
//     source.connect(offlineContext.destination);
//     source.start(0);

//     const renderedBuffer = await offlineContext.startRendering();
//     const samples = renderedBuffer.getChannelData(0);
//     const dataSize = samples.length * 2;

//     const wavBuffer = new ArrayBuffer(44 + dataSize);
//     const view = new DataView(wavBuffer);

//     function writeString(offset, string) {
//       for (let i = 0; i < string.length; i++) {
//         view.setUint8(offset + i, string.charCodeAt(i));
//       }
//     }

//     writeString(0, "RIFF");
//     view.setUint32(4, 36 + dataSize, true);
//     writeString(8, "WAVE");
//     writeString(12, "fmt ");
//     view.setUint32(16, 16, true);
//     view.setUint16(20, 1, true);
//     view.setUint16(22, 1, true);
//     view.setUint32(24, TARGET_SAMPLE_RATE, true);
//     view.setUint32(28, TARGET_SAMPLE_RATE * 2, true);
//     view.setUint16(32, 2, true);
//     view.setUint16(34, 16, true);
//     writeString(36, "data");
//     view.setUint32(40, dataSize, true);

//     let offset = 44;

//     for (let i = 0; i < samples.length; i++) {
//       const sample = Math.max(-1, Math.min(1, samples[i]));
//       view.setInt16(
//         offset,
//         sample < 0 ? sample * 32768 : sample * 32767,
//         true
//       );
//       offset += 2;
//     }

//     return new Blob([wavBuffer], { type: "audio/wav" });
//   } finally {
//     await audioContext.close();
//   }
// }

// function App() {
//   const [activePage, setActivePage] = useState("dashboard");
//   const [form, setForm] = useState(initialForm);
//   const [features, setFeatures] = useState(Array(23).fill("0").join(", "));
//   const [result, setResult] = useState(null);
//   const [loading, setLoading] = useState(false);
//   const [error, setError] = useState("");
//   const [transcript, setTranscript] = useState("Send 500 rupees to Rahul");

//   const [isRecording, setIsRecording] = useState(false);
//   const [voiceLoading, setVoiceLoading] = useState(false);
//   const [voiceStatus, setVoiceStatus] = useState("");
//   const [voiceError, setVoiceError] = useState("");

//   const mediaRecorderRef = useRef(null);
//   const audioChunksRef = useRef([]);
//   const streamRef = useRef(null);

//   const update = (key, value) => {
//     setForm((prev) => ({ ...prev, [key]: value }));
//     setResult(null);
//   };

//   async function startRecording() {
//     try {
//       setVoiceError("");
//       setVoiceStatus("");
//       setError("");

//       if (!navigator.mediaDevices?.getUserMedia) {
//         throw new Error("Microphone access requires localhost or HTTPS.");
//       }

//       if (!window.MediaRecorder) {
//         throw new Error("Audio recording is not supported by this browser.");
//       }

//       const stream = await navigator.mediaDevices.getUserMedia({
//         audio: {
//           channelCount: 1,
//           echoCancellation: true,
//           noiseSuppression: true,
//         },
//       });

//       streamRef.current = stream;
//       audioChunksRef.current = [];

//       const supportedTypes = [
//         "audio/webm;codecs=opus",
//         "audio/webm",
//         "audio/mp4",
//       ];

//       const mimeType = supportedTypes.find((type) =>
//         MediaRecorder.isTypeSupported(type)
//       );

//       const recorder = mimeType
//         ? new MediaRecorder(stream, { mimeType })
//         : new MediaRecorder(stream);

//       mediaRecorderRef.current = recorder;

//       recorder.ondataavailable = (event) => {
//         if (event.data?.size > 0) {
//           audioChunksRef.current.push(event.data);
//         }
//       };

//       recorder.onerror = () => {
//         setVoiceError("An error occurred during audio recording.");
//         setIsRecording(false);
//         setVoiceLoading(false);
//         stream.getTracks().forEach((track) => track.stop());
//         streamRef.current = null;
//       };

//       recorder.onstop = async () => {
//         stream.getTracks().forEach((track) => track.stop());
//         streamRef.current = null;

//         const audioBlob = new Blob(audioChunksRef.current, {
//           type: recorder.mimeType || "audio/webm",
//         });

//         if (!audioBlob.size) {
//           setVoiceError("No audio was recorded. Please try again.");
//           setVoiceLoading(false);
//           return;
//         }

//         await transcribeRecording(audioBlob);
//       };

//       recorder.start();
//       setIsRecording(true);
//       setResult(null);
//       setVoiceStatus("Listening... Speak your payment command.");
//     } catch (err) {
//       setVoiceError(err.message || "Unable to access the microphone.");
//       setVoiceStatus("");
//     }
//   }

//   function stopRecording() {
//     const recorder = mediaRecorderRef.current;

//     if (recorder && recorder.state === "recording") {
//       setIsRecording(false);
//       setVoiceLoading(true);
//       setVoiceStatus("Processing your voice...");
//       recorder.stop();
//     }
//   }

//   async function transcribeRecording(audioBlob) {
//     try {
//       setVoiceError("");
//       setVoiceStatus("Converting audio to WAV...");

//       const wavBlob = await convertToWav(audioBlob);

//       if (wavBlob.size > 10 * 1024 * 1024) {
//         throw new Error("Recording is too large. Keep it under 10 MB.");
//       }

//       const formData = new FormData();
//       formData.append("file", wavBlob, "recording.wav");

//       setVoiceStatus("Sending audio to Whisper Tiny...");

//       const response = await fetch(`${API_URL}/transcribe`, {
//         method: "POST",
//         body: formData,
//       });

//       const data = await response.json();

//       if (!response.ok) {
//         throw new Error(data.detail || "Transcription failed.");
//       }

//       if (!data.transcript) {
//         throw new Error("No speech could be recognized.");
//       }

//       setTranscript(data.transcript);
//       setResult(null);
//       setError("");

//       const extracted = extractPaymentDetails(data.transcript);

//       setForm((prev) => ({
//         ...prev,
//         ...(extracted.amount ? { amount: extracted.amount } : {}),
//         ...(extracted.recipient ? { recipient: extracted.recipient } : {}),
//         ...(extracted.unknownRecipient
//           ? {
//             recipientKnown: false,
//             recipientMatch: "0.20",
//           }
//           : {}),
//       }));

//       if (extracted.unknownRecipient) {
//         setVoiceStatus("Unknown recipient detected. Verify all details before assessment.");
//       } else if (extracted.amount || extracted.recipient) {
//         setVoiceStatus("Transcription complete. Review the extracted details before assessment.");
//       } else {
//         setVoiceStatus("Transcription complete. Check the transcript and enter details manually.");
//       }
//     } catch (err) {
//       setVoiceError(err.message || "Unable to transcribe the recording.");
//       setVoiceStatus("");
//     } finally {
//       setVoiceLoading(false);
//     }
//   }

//   async function assessPayment(event) {
//     event.preventDefault();
//     setLoading(true);
//     setError("");
//     setResult(null);

//     try {
//       const featureValues = features.split(",").map((value) => Number(value.trim()));

//       if (
//         featureValues.length !== 23 ||
//         featureValues.some((value) => !Number.isFinite(value))
//       ) {
//         throw new Error("Enter exactly 23 valid numeric transaction features.");
//       }

//       if (!Number.isFinite(Number(form.amount)) || Number(form.amount) <= 0) {
//         throw new Error("Enter a valid payment amount.");
//       }

//       if (
//         !Number.isFinite(Number(form.typicalAmount)) ||
//         Number(form.typicalAmount) <= 0
//       ) {
//         throw new Error("Enter a valid typical payment amount.");
//       }

//       const response = await fetch(`${API_URL}/predict-context`, {
//         method: "POST",
//         headers: { "Content-Type": "application/json" },
//         body: JSON.stringify({
//           transaction_features: featureValues,
//           context: {
//             recipient_is_known: form.recipientKnown,
//             amount: Number(form.amount),
//             typical_amount: Number(form.typicalAmount),
//             recipient_match_confidence: Number(form.recipientMatch),
//             voice_intent_confidence: Number(form.voiceConfidence),
//           },
//         }),
//       });

//       const data = await response.json();

//       if (!response.ok) {
//         throw new Error(data.detail || "Risk assessment failed.");
//       }

//       setResult(data);
//     } catch (err) {
//       setError(
//         err.message.includes("fetch")
//           ? "Cannot connect to the backend. Ensure FastAPI is running."
//           : err.message
//       );
//     } finally {
//       setLoading(false);
//     }
//   }

//   const risk = result?.risk_level?.toUpperCase() || "";
//   const riskClass = risk.toLowerCase();
//   const decision = result?.risk_decision || result?.decision || "AWAITING ASSESSMENT";

//   const formatAmount = (value) =>
//     Number(value || 0).toLocaleString("en-IN", {
//       maximumFractionDigits: 2,
//     });

//   const goTo = (page) => {
//     setActivePage(page);
//     window.scrollTo({ top: 0, behavior: "smooth" });
//   };

//   return (
//     <div className="app-shell">
//       <aside className="sidebar">
//         <a className="brand" href="#home" onClick={(e) => { e.preventDefault(); goTo("dashboard"); }}>
//           <span className="brand-icon">V</span>
//           <span className="brand-copy">
//             VeriPay
//             <small>VERIFY BEFORE YOU PAY</small>
//           </span>
//         </a>

//         <div className="side-label">MENU</div>

//         <button className={`nav-item ${activePage === "dashboard" ? "active" : ""}`} onClick={() => goTo("dashboard")}>
//           <span>⌂</span> Dashboard
//         </button>

//         <button className={`nav-item ${activePage === "payment" ? "active" : ""}`} onClick={() => goTo("payment")}>
//           <span>＋</span> New payment
//         </button>

//         <button className={`nav-item ${activePage === "security" ? "active" : ""}`} onClick={() => goTo("security")}>
//           <span>◈</span> Security insights
//         </button>

//         <div className="sidebar-bottom">
//           <div className="sidebar-shield">✳</div>
//           <strong>Your safety comes first.</strong>
//           <p>Every payment deserves a second look.</p>
//           <span className="offline-tag">DEMO MODE · NO MONEY MOVES</span>
//         </div>
//       </aside>

//       <main className="main-content">
//         <header className="topbar">
//           <div>
//             <span className="topbar-kicker">VERIPAY</span>
//             <span className="topbar-divider">/</span>
//             <span>
//               {activePage === "dashboard"
//                 ? "Dashboard"
//                 : activePage === "payment"
//                   ? "New Payment"
//                   : "Security Insights"}
//             </span>
//           </div>
//           <div className="system-status"><i /> CPDE SYSTEM · LOCAL</div>
//         </header>

//         {activePage === "dashboard" && (
//           <div className="page dashboard-page">
//             <section className="dashboard-welcome">
//               <div>
//                 <span className="eyebrow">YOUR PAYMENT SECURITY SPACE</span>
//                 <h1>Welcome to <span>VeriPay.</span></h1>
//                 <p>
//                   Your voice. Your payments. Your control.
//                   Make informed payment decisions with context-aware security.
//                 </p>
//                 <button className="primary-button dashboard-cta" onClick={() => goTo("payment")}>
//                   Start a new assessment <span>→</span>
//                 </button>
//               </div>
//               <div className="dashboard-emblem">
//                 <div className="emblem-ring">
//                   <div className="emblem-shield">✓</div>
//                 </div>
//                 <span>VERIFY BEFORE YOU PAY</span>
//               </div>
//             </section>

//             <section className="dashboard-section">
//               <div className="section-heading">
//                 <div>
//                   <span className="eyebrow">AT A GLANCE</span>
//                   <h2>Your security overview</h2>
//                   <p>The core safeguards behind every assessment.</p>
//                 </div>
//               </div>

//               <div className="overview-grid">
//                 <article className="overview-card">
//                   <div className="overview-icon purple">◈</div>
//                   <div><span className="card-overline">DECISION ENGINE</span><h3>CPDE</h3><p>Context-aware risk evaluation</p></div>
//                 </article>
//                 <article className="overview-card">
//                   <div className="overview-icon blue">⌁</div>
//                   <div><span className="card-overline">CONTEXT SIGNALS</span><h3>05 signals</h3><p>Recipient, amount, voice and more</p></div>
//                 </article>
//                 <article className="overview-card">
//                   <div className="overview-icon green">✓</div>
//                   <div><span className="card-overline">PAYMENT EXECUTION</span><h3 className="safe-text">Disabled</h3><p>No real transfers are initiated</p></div>
//                 </article>
//               </div>
//             </section>

//             <section className="dashboard-lower">
//               <article className="panel quick-panel">
//                 <span className="eyebrow">QUICK ACTION</span>
//                 <h2>Ready to verify a payment?</h2>
//                 <p>Speak naturally, review the extracted payment details and let the decision engine assess contextual risk.</p>
//                 <button className="primary-button" onClick={() => goTo("payment")}>
//                   ＋ New payment assessment
//                 </button>
//               </article>

//               <article className="panel recent-panel">
//                 <span className="eyebrow">LATEST ASSESSMENT</span>
//                 {result ? (
//                   <>
//                     <div className={`recent-risk ${riskClass}`}>{risk || "UNKNOWN"} RISK</div>
//                     <h3>{form.recipient}</h3>
//                     <p>Payment amount: ₹{formatAmount(form.amount)}</p>
//                     <p>Recommended action: {decision}</p>
//                     <button className="text-button" onClick={() => goTo("payment")}>View assessment →</button>
//                   </>
//                 ) : (
//                   <>
//                     <div className="recent-empty-icon">◷</div>
//                     <h3>No assessment yet</h3>
//                     <p>Your latest assessment will appear here.</p>
//                     <button className="text-button" onClick={() => goTo("payment")}>Start your first assessment →</button>
//                   </>
//                 )}
//               </article>
//             </section>
//           </div>
//         )}

//         {activePage === "payment" && (
//           <div className="page payment-page">
//             <section className="page-intro">
//               <span className="eyebrow">VOICE-FIRST PAYMENT SECURITY</span>
//               <h1>Let's verify your <span>payment.</span></h1>
//               <p>Tell VeriPay what you want to pay. Review the details before evaluating the transaction.</p>
//             </section>

//             <section className="payment-layout">
//               <article className="panel payment-panel">
//                 <div className="panel-heading">
//                   <div className="panel-icon">↗</div>
//                   <div><h3>Payment details</h3><p>Enter or speak your payment command.</p></div>
//                 </div>

//                 <div className="voice-card">
//                   <div className="voice-card-top">
//                     <div><span className="card-overline">VOICE ASSISTANT</span><h3>Speak your payment</h3><p>Use natural language to describe your transaction.</p></div>
//                     <div className="voice-wave-icon">〰</div>
//                   </div>

//                   <div className={`voice-visual ${isRecording ? "active" : ""}`}>
//                     <div className="voice-mic">{isRecording ? "■" : "🎙"}</div>
//                     <div>
//                       <strong>{isRecording ? "Listening to you..." : voiceLoading ? "Processing voice..." : "Ready to listen"}</strong>
//                       <span>{isRecording ? "Speak clearly into your microphone" : "Tap the button below to start"}</span>
//                     </div>
//                     {isRecording && <div className="recording-dot" />}
//                   </div>

//                   <div className="voice-controls">
//                     {!isRecording ? (
//                       <button type="button" className="voice-button" onClick={startRecording} disabled={voiceLoading}>
//                         🎙 {voiceLoading ? "Processing..." : "Start recording"}
//                       </button>
//                     ) : (
//                       <button type="button" className="voice-button recording" onClick={stopRecording}>■ Stop recording</button>
//                     )}
//                     <span className="voice-hint">Microphone access required</span>
//                   </div>

//                   {voiceStatus && <p className="voice-note">{voiceStatus}</p>}
//                   {voiceError && <p className="voice-error">{voiceError}</p>}
//                 </div>

//                 <form onSubmit={assessPayment}>
//                   <div className="form-section-title"><span>01</span><div><h4>Review your command</h4><p>Check the transcript before continuing.</p></div></div>
//                   <label htmlFor="transcript">Voice command transcript</label>
//                   <textarea id="transcript" rows="2" value={transcript} onChange={(e) => setTranscript(e.target.value)} placeholder="Example: Send 500 rupees to Rahul" />

//                   <div className="form-section-title"><span>02</span><div><h4>Payment information</h4><p>Verify the recipient and amount carefully.</p></div></div>

//                   <div className="form-row">
//                     <div><label htmlFor="recipient">Recipient</label><input id="recipient" value={form.recipient} onChange={(e) => update("recipient", e.target.value)} required /></div>
//                     <div><label htmlFor="amount">Amount (INR)</label><input id="amount" type="number" min="0.01" step="0.01" value={form.amount} onChange={(e) => update("amount", e.target.value)} required /></div>
//                   </div>

//                   <label htmlFor="typicalAmount">Your typical payment amount (INR)</label>
//                   <input id="typicalAmount" type="number" min="0.01" step="0.01" value={form.typicalAmount} onChange={(e) => update("typicalAmount", e.target.value)} required />

//                   <label className="toggle-row">
//                     <span><strong>Known recipient</strong><small>Is this person in your trusted contacts?</small></span>
//                     <input type="checkbox" checked={form.recipientKnown} onChange={(e) => update("recipientKnown", e.target.checked)} />
//                   </label>

//                   <details className="advanced">
//                     <summary>Advanced assessment inputs</summary>
//                     <p>Additional values supplied to the assessment.</p>
//                     <div className="form-row">
//                       <div><label htmlFor="match">Recipient match confidence</label><input id="match" type="number" min="0" max="1" step="0.01" value={form.recipientMatch} onChange={(e) => update("recipientMatch", e.target.value)} /></div>
//                       <div><label htmlFor="confidence">Voice intent confidence</label><input id="confidence" type="number" min="0" max="1" step="0.01" value={form.voiceConfidence} onChange={(e) => update("voiceConfidence", e.target.value)} /></div>
//                     </div>
//                     <label htmlFor="features">23 transaction model features</label>
//                     <textarea id="features" rows="3" value={features} onChange={(e) => setFeatures(e.target.value)} />
//                     <small className="advanced-note">Initialized with zeros. Replace with correctly mapped features for meaningful model predictions.</small>
//                   </details>

//                   {error && <div className="error-message">{error}</div>}

//                   <button className="primary-button" type="submit" disabled={loading || isRecording || voiceLoading}>
//                     {loading ? "Evaluating payment risk..." : "Evaluate payment risk"} <span>→</span>
//                   </button>
//                   <p className="disclaimer">VeriPay evaluates risk only. It does not initiate or authorize a UPI payment.</p>
//                 </form>
//               </article>

//               <div className="right-column">
//                 <article className="panel decision-panel">
//                   <div className="panel-heading">
//                     <div className="panel-icon">◎</div>
//                     <div><h3>Risk decision</h3><p>CPDE assessment and recommended action.</p></div>
//                   </div>

//                   {!result && !loading && (
//                     <div className="empty-state">
//                       <div className="empty-illustration"><div className="empty-shield">✓</div></div>
//                       <span className="card-overline">AWAITING ASSESSMENT</span>
//                       <h3>Your decision will appear here.</h3>
//                       <p>Complete the payment details and evaluate the transaction to view its risk level and recommended action.</p>
//                     </div>
//                   )}

//                   {loading && (
//                     <div className="loading-state"><div className="loader-ring" /><h3>Evaluating transaction</h3><p>Analysing contextual risk signals...</p></div>
//                   )}

//                   {result && (
//                     <div className="result-content">
//                       <div className={`risk-banner ${riskClass}`}>
//                         <div className="risk-symbol">{risk === "HIGH" ? "!" : risk === "MEDIUM" ? "◇" : "✓"}</div>
//                         <div><span className="card-overline">ASSESSED RISK</span><h2>{risk || "UNKNOWN"} RISK</h2><p>{result.reason || "Review the decision details."}</p></div>
//                       </div>

//                       <div className="transaction-summary">
//                         <div><span>RECIPIENT</span><strong>{form.recipient || "Not specified"}</strong></div>
//                         <div><span>PAYMENT AMOUNT</span><strong>₹{formatAmount(form.amount)}</strong></div>
//                       </div>

//                       <div className="metric-grid">
//                         <div className="metric"><span>Fraud probability</span><strong>{Number.isFinite(Number(result.fraud_probability)) ? `${(Number(result.fraud_probability) * 100).toFixed(2)}%` : "N/A"}</strong></div>
//                         <div className="metric"><span>Context risk score</span><strong>{Number.isFinite(Number(result.context_score)) ? `${(Number(result.context_score) * 100).toFixed(1)}%` : "N/A"}</strong></div>
//                       </div>

//                       <div className="signals-heading"><h4>Contextual risk signals</h4><span>CPDE ANALYSIS</span></div>
//                       <div className="signal-list">
//                         {Object.entries(result.context_signals || {}).map(([key, value]) => (
//                           <div className="signal-row" key={key}><span>{key.replaceAll("_", " ")}</span><strong>{Number.isFinite(Number(value)) ? Number(value).toFixed(2) : String(value)}</strong></div>
//                         ))}
//                         {!Object.keys(result.context_signals || {}).length && <p className="no-signals">No contextual signals returned.</p>}
//                       </div>

//                       <div className="decision-box"><span>RECOMMENDED ACTION</span><strong>{decision}</strong><p>{result.payment_decision || "Review the assessment."}</p></div>
//                       <div className="execution-note"><span>✓</span> Payment execution: <strong>{result.payment_execution || "NOT_EXECUTED"}</strong></div>
//                       {result.confirmation_required && <p className="confirmation-note">Explicit confirmation is required before any future payment workflow could proceed.</p>}
//                     </div>
//                   )}
//                 </article>

//                 <article className="panel safety-note">
//                   <div className="panel-icon">✳</div>
//                   <div><h3>Safety by design</h3><p>Every result is an assessment recommendation. No money is transferred by this prototype.</p></div>
//                 </article>
//               </div>
//             </section>
//           </div>
//         )}

//         {activePage === "security" && (
//           <div className="page security-page">
//             <section className="page-intro">
//               <span className="eyebrow">INSIDE THE DECISION ENGINE</span>
//               <h1>Security <span>insights.</span></h1>
//               <p>Understand the contextual signals and safeguards that contribute to a payment decision.</p>
//             </section>

//             <section className="security-hero panel">
//               <div className="security-hero-icon">✳</div>
//               <div>
//                 <span className="eyebrow">CONTEXT-AWARE PAYMENT DECISION ENGINE</span>
//                 <h2>Verify the context, not just the transaction.</h2>
//                 <p>VeriPay combines recipient information, payment behaviour, voice intent and transaction features to recommend a safer action.</p>
//               </div>
//             </section>

//             <div className="security-grid">
//               {[
//                 ["01", "Recipient familiarity", "Checks whether the recipient is known to the user."],
//                 ["02", "Payment deviation", "Compares the proposed amount with the user's typical payment amount."],
//                 ["03", "Recipient matching", "Considers the confidence associated with identifying the recipient."],
//                 ["04", "Voice intent", "Uses the supplied voice intent confidence value."],
//                 ["05", "Transaction risk", "Evaluates the supplied transaction model features."],
//               ].map(([number, title, description]) => (
//                 <article className="panel security-feature" key={number}>
//                   <span className="security-number">{number}</span>
//                   <div className="feature-icon">◇</div>
//                   <h3>{title}</h3>
//                   <p>{description}</p>
//                 </article>
//               ))}
//             </div>

//             <article className="panel decision-explainer">
//               <span className="eyebrow">DECISION POLICY</span>
//               <h2>How VeriPay responds</h2>
//               <div className="decision-levels">
//                 <div className="decision-level proceed"><span>✓</span><div><strong>PROCEED</strong><p>Low contextual risk; recommendation to proceed subject to explicit confirmation.</p></div></div>
//                 <div className="decision-level warn"><span>!</span><div><strong>WARN</strong><p>Elevated risk; the user should review the transaction carefully.</p></div></div>
//                 <div className="decision-level block"><span>×</span><div><strong>BLOCK</strong><p>High risk; the transaction should not proceed.</p></div></div>
//                 <div className="decision-level clarify"><span>?</span><div><strong>REQUEST CLARIFICATION</strong><p>Payment details or recipient information need clarification.</p></div></div>
//               </div>
//             </article>

//             <article className="panel execution-disclaimer">
//               <strong>Payment execution is disabled.</strong>
//               <p>VeriPay is a research prototype. Its decisions are recommendations only and do not initiate or authorize real UPI transfers.</p>
//             </article>
//           </div>
//         )}

//         <footer className="footer">
//           <span>VeriPay <i>·</i> Context-Aware Payment Decision Engine</span>
//           <span>Research prototype <i>·</i> No live payment integration</span>
//         </footer>
//       </main>
//     </div>
//   );
// }

// export default App;

import { useState, useRef, useEffect } from "react";
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

function parseSpokenNumber(text) {
  const words = text.toLowerCase().replace(/-/g, " ").split(/\s+/);

  const numbers = {
    zero: 0, one: 1, two: 2, three: 3, four: 4,
    five: 5, six: 6, seven: 7, eight: 8, nine: 9,
    ten: 10, eleven: 11, twelve: 12, thirteen: 13,
    fourteen: 14, fifteen: 15, sixteen: 16,
    seventeen: 17, eighteen: 18, nineteen: 19,
    twenty: 20, thirty: 30, forty: 40, fifty: 50,
    sixty: 60, seventy: 70, eighty: 80, ninety: 90,
  };

  const directNumber = text.match(/\d+(?:\.\d+)?/);

  if (directNumber) {
    return Number(directNumber[0]);
  }

  let total = 0;
  let current = 0;

  for (const word of words) {
    if (numbers[word] !== undefined) {
      current += numbers[word];
    } else if (word === "hundred") {
      current = (current || 1) * 100;
    } else if (word === "thousand") {
      total += (current || 1) * 1000;
      current = 0;
    }
  }

  total += current;
  return total || null;
}

function extractPaymentDetails(transcript) {
  const text = transcript.toLowerCase();

  const amountMatch = text.match(
    /(?:rupees?|rs\.?|inr)\s*(\d+(?:\.\d+)?)|(\d+(?:\.\d+)?)\s*(?:rupees?|rs\.?|inr)/
  );

  let amount = null;

  if (amountMatch) {
    amount = Number(amountMatch[1] || amountMatch[2]);
  } else {
    const number = parseSpokenNumber(text);
    if (number) amount = number;
  }

  const recipientMatch = transcript.match(
    /(?:to|pay|send|transfer)\s+(?:the\s+)?([a-zA-Z]+(?:\s+[a-zA-Z]+){0,2})/i
  );

  const recipient = recipientMatch
    ? recipientMatch[1].trim()
    : null;

  return {
    amount,
    recipient,
  };
}

async function convertToWav(audioBlob) {
  const audioContext = new AudioContext();
  const arrayBuffer = await audioBlob.arrayBuffer();

  const audioBuffer = await audioContext.decodeAudioData(arrayBuffer);

  const offlineContext = new OfflineAudioContext(
    1,
    Math.ceil(audioBuffer.duration * TARGET_SAMPLE_RATE),
    TARGET_SAMPLE_RATE
  );

  const source = offlineContext.createBufferSource();
  source.buffer = audioBuffer;

  source.connect(offlineContext.destination);
  source.start(0);

  const renderedBuffer = await offlineContext.startRendering();

  const samples = renderedBuffer.getChannelData(0);

  const buffer = new ArrayBuffer(44 + samples.length * 2);
  const view = new DataView(buffer);

  function writeString(offset, value) {
    for (let i = 0; i < value.length; i++) {
      view.setUint8(offset + i, value.charCodeAt(i));
    }
  }

  writeString(0, "RIFF");
  view.setUint32(4, 36 + samples.length * 2, true);
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
  view.setUint32(40, samples.length * 2, true);

  let offset = 44;

  for (let i = 0; i < samples.length; i++) {
    const sample = Math.max(-1, Math.min(1, samples[i]));

    view.setInt16(
      offset,
      sample < 0 ? sample * 0x8000 : sample * 0x7fff,
      true
    );

    offset += 2;
  }

  await audioContext.close();

  return new Blob([buffer], { type: "audio/wav" });
}

function App() {
  const [activePage, setActivePage] = useState("dashboard");

  const [form, setForm] = useState(initialForm);

  const [features, setFeatures] = useState(
    Array(23).fill("0").join(", ")
  );

  const [result, setResult] = useState(null);
  const [voiceResult, setVoiceResult] = useState(null);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const [transcript, setTranscript] = useState("");
  const [isRecording, setIsRecording] = useState(false);
  const [voiceLoading, setVoiceLoading] = useState(false);
  const [voiceStatus, setVoiceStatus] = useState("");
  const [voiceError, setVoiceError] = useState("");

  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const streamRef = useRef(null);
  const [mobileNavOpen, setMobileNavOpen] = useState(false);

  useEffect(() => {
    if (mobileNavOpen) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "";
    }

    const handleKeyDown = (e) => {
      if (e.key === "Escape" && mobileNavOpen) {
        setMobileNavOpen(false);
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => {
      document.body.style.overflow = "";
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, [mobileNavOpen]);

  function goTo(page) {
    setActivePage(page);
    setMobileNavOpen(false);
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  function update(field, value) {
    setForm((prev) => ({
      ...prev,
      [field]: value,
    }));

    setResult(null);
    setVoiceResult(null);
    setVoiceStatus("");
    setVoiceError("");
    setError("");
  }

  async function startRecording() {
    try {
      setVoiceError("");
      setVoiceStatus("");

      setTranscript("");
      setVoiceResult(null);
      setResult(null);

      setVoiceLoading(true);

      if (!navigator.mediaDevices?.getUserMedia) {
        throw new Error(
          "Microphone access is unavailable in this browser."
        );
      }

      const stream = await navigator.mediaDevices.getUserMedia({
        audio: true,
      });

      streamRef.current = stream;
      audioChunksRef.current = [];

      const mimeType = MediaRecorder.isTypeSupported(
        "audio/webm;codecs=opus"
      )
        ? "audio/webm;codecs=opus"
        : "audio/webm";

      const recorder = new MediaRecorder(stream, { mimeType });

      mediaRecorderRef.current = recorder;

      recorder.ondataavailable = (event) => {
        if (event.data?.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      recorder.onerror = () => {
        setVoiceError("An error occurred during audio recording.");
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
          setVoiceError("No audio was recorded. Please try again.");
          setVoiceLoading(false);
          return;
        }

        await transcribeRecording(audioBlob);
      };

      recorder.start();

      setIsRecording(true);
      setVoiceLoading(false);
      setVoiceStatus("Listening... Speak your payment command.");
    } catch (err) {
      setVoiceError(
        err.message || "Unable to access the microphone."
      );

      setVoiceStatus("");
      setVoiceLoading(false);
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

      setVoiceStatus(
        "Sending audio to the voice payment engine..."
      );

      const response = await fetch(`${API_URL}/voice-payment`, {
        method: "POST",
        body: formData,
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail || "Voice assessment failed."
        );
      }

      if (!data.transcript) {
        throw new Error("No speech could be recognized.");
      }

      setTranscript(data.transcript);
      setVoiceResult(data);
      setResult(null);
      setError("");

      setForm((prev) => ({
        ...prev,
        recipient:
          data.intent?.recipient_name || prev.recipient,
        amount:
          data.intent?.amount != null
            ? String(data.intent.amount)
            : prev.amount,
        recipientKnown:
          data.status === "ASSESSMENT_COMPLETED",
      }));

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

      throw new Error(
        "Unexpected response from the voice payment service."
      );
    } catch (err) {
      setVoiceError(
        err.message || "Unable to process the recording."
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
      const parsedFeatures = features
        .split(",")
        .map((value) => Number(value.trim()));

      if (
        parsedFeatures.length !== 23 ||
        parsedFeatures.some((value) => !Number.isFinite(value))
      ) {
        throw new Error(
          "Please provide exactly 23 valid numeric transaction features."
        );
      }

      const payload = {
        recipient_name: form.recipient,
        amount: Number(form.amount),
        typical_amount: Number(form.typicalAmount),
        recipient_known: form.recipientKnown,
        recipient_match_confidence: Number(
          form.recipientMatch
        ),
        voice_intent_confidence: Number(
          form.voiceConfidence
        ),
        transaction_features: parsedFeatures,
      };

      const response = await fetch(
        `${API_URL}/predict-context`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(payload),
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail || "Unable to evaluate payment risk."
        );
      }

      setResult(data);
      setVoiceResult(null);
    } catch (err) {
      setError(
        err.message ||
        "Something went wrong while assessing the payment."
      );
    } finally {
      setLoading(false);
    }
  }

  function formatAmount(value) {
    const number = Number(value);

    if (!Number.isFinite(number)) {
      return value || "0";
    }

    return number.toLocaleString("en-IN", {
      maximumFractionDigits: 2,
    });
  }

  const risk =
    result?.risk_level ||
    result?.risk ||
    result?.risk_category ||
    "";

  const riskClass =
    risk === "HIGH"
      ? "risk-high"
      : risk === "MEDIUM"
        ? "risk-medium"
        : "risk-low";

  const decision =
    result?.decision ||
    result?.recommended_action ||
    result?.payment_decision ||
    "REVIEW";

  return (
    <div className="app-shell">
      {/* Mobile Drawer Backdrop */}
      <div
        className={`sidebar-backdrop ${mobileNavOpen ? "open" : ""}`}
        onClick={() => setMobileNavOpen(false)}
        aria-hidden="true"
      />

      <aside className={`sidebar ${mobileNavOpen ? "open" : ""}`}>
        <div className="sidebar-header">
          <div
            className="brand"
            onClick={() => goTo("dashboard")}
            role="button"
            tabIndex={0}
          >
            <div className="brand-mark">V</div>

            <div>
              <h2>VeriPay</h2>
              <span>VERIFY BEFORE YOU PAY</span>
            </div>
          </div>

          <button
            type="button"
            className="sidebar-close-btn"
            onClick={() => setMobileNavOpen(false)}
            aria-label="Close navigation menu"
          >
            ✕
          </button>
        </div>

        <div className="sidebar-label">WORKSPACE</div>

        <nav className="sidebar-nav">
          <button
            className={
              activePage === "dashboard"
                ? "nav-item active"
                : "nav-item"
            }
            onClick={() => goTo("dashboard")}
          >
            <span className="nav-icon">⌂</span>
            <span>Dashboard</span>
          </button>

          <button
            className={
              activePage === "payment"
                ? "nav-item active"
                : "nav-item"
            }
            onClick={() => goTo("payment")}
          >
            <span className="nav-icon">↗</span>
            <span>Payment check</span>
          </button>

          <button
            className={
              activePage === "security"
                ? "nav-item active"
                : "nav-item"
            }
            onClick={() => goTo("security")}
          >
            <span className="nav-icon">◇</span>
            <span>Security insights</span>
          </button>
        </nav>

        <div className="sidebar-bottom">
          <div className="sidebar-status">
            <span className="status-dot"></span>

            <div>
              <strong>CPDE engine</strong>
              <small>Risk assessment prototype</small>
            </div>
          </div>

          <div className="sidebar-user">
            <div className="avatar">S</div>

            <div>
              <strong>Demo user</strong>
              <small>Personal account</small>
            </div>

            <span className="more-icon">···</span>
          </div>
        </div>
      </aside>

      <main className="main-content">
        <header className="topbar">
          <div className="topbar-left">
            <button
              type="button"
              className="hamburger-btn"
              onClick={() => setMobileNavOpen((prev) => !prev)}
              aria-label="Open navigation menu"
              aria-expanded={mobileNavOpen}
            >
              <span className="hamburger-line"></span>
              <span className="hamburger-line"></span>
              <span className="hamburger-line"></span>
            </button>

            <div className="breadcrumb">
              <span className="breadcrumb-root">Workspace</span>
              <span className="breadcrumb-separator">/</span>
              <span className="breadcrumb-current">
                {activePage === "dashboard"
                  ? "Dashboard"
                  : activePage === "payment"
                    ? "Payment check"
                    : "Security insights"}
              </span>
            </div>
          </div>

          <div className="topbar-right">
            <span className="prototype-pill">
              <span className="prototype-dot"></span>
              <span className="prototype-text">PROTOTYPE MODE</span>
            </span>

            <div className="topbar-avatar" title="Demo user (Personal account)">S</div>
          </div>
        </header>

        {activePage === "dashboard" && (
          <div className="page dashboard-page">
            <section className="hero-section">
              <div className="hero-copy">
                <span className="eyebrow">
                  CONTEXT-AWARE PAYMENT SECURITY
                </span>

                <h1>
                  A smarter way to <span>pay safely.</span>
                </h1>

                <p>
                  VeriPay analyses payment intent and contextual
                  risk signals to help identify suspicious
                  transactions before payment.
                </p>

                <button
                  className="primary-button"
                  onClick={() => goTo("payment")}
                >
                  Check a payment <span>→</span>
                </button>
              </div>

              <div className="hero-visual">
                <div className="hero-orbit orbit-one"></div>
                <div className="hero-orbit orbit-two"></div>

                <div className="hero-shield">
                  <span>✓</span>
                </div>

                <div className="floating-chip chip-one">
                  <span className="chip-dot"></span>
                  Intent verified
                </div>

                <div className="floating-chip chip-two">
                  <span className="chip-dot"></span>
                  Risk analysed
                </div>
              </div>
            </section>

            <section className="stats-grid">
              <article className="panel stat-card">
                <span className="stat-icon">◎</span>
                <span className="card-overline">
                  DECISION ENGINE
                </span>
                <h3>CPDE</h3>
                <p>Context-aware assessment</p>
              </article>

              <article className="panel stat-card">
                <span className="stat-icon">⌁</span>
                <span className="card-overline">
                  INPUT METHOD
                </span>
                <h3>Voice + Form</h3>
                <p>Natural payment commands</p>
              </article>

              <article className="panel stat-card">
                <span className="stat-icon">◇</span>
                <span className="card-overline">
                  SAFETY ACTIONS
                </span>
                <h3>3 Levels</h3>
                <p>Proceed, warn or block</p>
              </article>
            </section>

            <section className="dashboard-section">
              <div className="section-heading">
                <div>
                  <span className="eyebrow">
                    RECENT ACTIVITY
                  </span>

                  <h2>Latest assessment</h2>

                  <p>
                    Your most recent payment risk evaluation.
                  </p>
                </div>

                <button
                  className="text-button"
                  onClick={() => goTo("payment")}
                >
                  New assessment →
                </button>
              </div>

              <article className="panel recent-panel">
                {!result ? (
                  <div className="recent-empty">
                    <span className="recent-empty-icon">◷</span>

                    <div>
                      <strong>No assessment yet</strong>
                      <p>
                        Your latest risk assessment will appear
                        here.
                      </p>
                    </div>
                  </div>
                ) : (
                  <div className="recent-result">
                    <div>
                      <span className="card-overline">
                        LATEST DECISION
                      </span>

                      <h3>{risk || "UNKNOWN"} RISK</h3>

                      <p>
                        {result.reason ||
                          "Assessment completed."}
                      </p>
                    </div>

                    <div className={`recent-risk ${riskClass}`}>
                      {decision}
                    </div>

                    <button
                      className="text-button"
                      onClick={() => goTo("payment")}
                    >
                      View details →
                    </button>
                  </div>
                )}
              </article>
            </section>
          </div>
        )}

        {activePage === "payment" && (
          <div className="page payment-page">
            <section className="page-intro">
              <span className="eyebrow">
                CONTEXT-AWARE PAYMENT CHECK
              </span>

              <h1>
                Verify before <span>you pay.</span>
              </h1>

              <p>
                Enter payment details or speak your payment
                command. VeriPay will evaluate the context
                before recommending an action.
              </p>
            </section>

            <section className="payment-layout">
              <article className="panel payment-form-panel">
                <div className="panel-heading">
                  <div className="panel-icon">↗</div>

                  <div>
                    <h3>Payment details</h3>
                    <p>
                      Provide the transaction information for
                      assessment.
                    </p>
                  </div>
                </div>

                <div className="voice-box">
                  <div className="voice-box-top">
                    <div>
                      <span className="card-overline">
                        VOICE PAYMENT INPUT
                      </span>

                      <h3>Speak your payment.</h3>

                      <p>
                        Try saying: “Send 500 rupees to Rahul.”
                      </p>
                    </div>

                    <div
                      className={`voice-indicator ${isRecording ? "recording" : ""
                        }`}
                    >
                      <span></span>
                    </div>
                  </div>

                  <div className="voice-controls">
                    {!isRecording ? (
                      <button
                        type="button"
                        className="voice-button"
                        onClick={startRecording}
                        disabled={voiceLoading}
                      >
                        <span>🎙</span>

                        {voiceLoading
                          ? "Processing..."
                          : "Start recording"}
                      </button>
                    ) : (
                      <button
                        type="button"
                        className="voice-button recording-button"
                        onClick={stopRecording}
                      >
                        <span>■</span> Stop recording
                      </button>
                    )}
                  </div>

                  {voiceStatus && (
                    <p className="voice-note">{voiceStatus}</p>
                  )}

                  {voiceError && (
                    <p className="voice-error">{voiceError}</p>
                  )}

                  {voiceResult && (
                    <div className="voice-note">
                      <strong>
                        Voice pipeline: {voiceResult.status}
                      </strong>

                      {voiceResult.intent?.recipient_name && (
                        <p>
                          Recipient detected:{" "}
                          {voiceResult.intent.recipient_name}
                        </p>
                      )}

                      {voiceResult.intent?.amount != null && (
                        <p>
                          Amount detected: ₹
                          {voiceResult.intent.amount}
                        </p>
                      )}

                      {voiceResult.reason && (
                        <p>{voiceResult.reason}</p>
                      )}
                    </div>
                  )}

                  {transcript && (
                    <div className="transcript-box">
                      <span>RECOGNISED SPEECH</span>
                      <p>“{transcript}”</p>
                    </div>
                  )}
                </div>

                <form
                  onSubmit={assessPayment}
                  className="payment-form"
                >
                  <div className="form-section-title">
                    <span>01</span>

                    <div>
                      <h4>Transaction information</h4>

                      <p>
                        Confirm the recipient and payment
                        amount.
                      </p>
                    </div>
                  </div>

                  <div className="form-row">
                    <div>
                      <label htmlFor="recipient">
                        Recipient name
                      </label>

                      <input
                        id="recipient"
                        type="text"
                        value={form.recipient}
                        onChange={(e) =>
                          update("recipient", e.target.value)
                        }
                        placeholder="e.g. Rahul Sharma"
                        required
                      />
                    </div>

                    <div>
                      <label htmlFor="amount">
                        Payment amount (INR)
                      </label>

                      <input
                        id="amount"
                        type="number"
                        min="0.01"
                        step="0.01"
                        value={form.amount}
                        onChange={(e) =>
                          update("amount", e.target.value)
                        }
                        required
                      />
                    </div>
                  </div>

                  <div className="form-section-title second-section-title">
                    <span>02</span>

                    <div>
                      <h4>Contextual information</h4>

                      <p>
                        Help the engine understand your usual
                        payment behaviour.
                      </p>
                    </div>
                  </div>

                  <label htmlFor="typicalAmount">
                    Your typical payment amount (INR)
                  </label>

                  <input
                    id="typicalAmount"
                    type="number"
                    min="0.01"
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
                        Is this person in your trusted contacts?
                      </small>
                    </span>

                    <input
                      type="checkbox"
                      checked={form.recipientKnown}
                      onChange={(e) =>
                        update(
                          "recipientKnown",
                          e.target.checked
                        )
                      }
                    />
                  </label>

                  <details className="advanced">
                    <summary>Advanced assessment inputs</summary>

                    <p>
                      Additional values supplied to the
                      assessment.
                    </p>

                    <div className="form-row">
                      <div>
                        <label htmlFor="match">
                          Recipient match confidence
                        </label>

                        <input
                          id="match"
                          type="number"
                          min="0"
                          max="1"
                          step="0.01"
                          value={form.recipientMatch}
                          onChange={(e) =>
                            update(
                              "recipientMatch",
                              e.target.value
                            )
                          }
                        />
                      </div>

                      <div>
                        <label htmlFor="confidence">
                          Voice intent confidence
                        </label>

                        <input
                          id="confidence"
                          type="number"
                          min="0"
                          max="1"
                          step="0.01"
                          value={form.voiceConfidence}
                          onChange={(e) =>
                            update(
                              "voiceConfidence",
                              e.target.value
                            )
                          }
                        />
                      </div>
                    </div>

                    <label htmlFor="features">
                      23 transaction model features
                    </label>

                    <textarea
                      id="features"
                      rows="3"
                      value={features}
                      onChange={(e) =>
                        setFeatures(e.target.value)
                      }
                    />

                    <small className="advanced-note">
                      Initialized with zeros. Replace with
                      correctly mapped features for meaningful
                      model predictions.
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
                      voiceResult?.status ===
                      "CLARIFICATION_REQUIRED" ||
                      voiceResult?.status ===
                      "VERIFICATION_REQUIRED"
                    }
                  >
                    {loading
                      ? "Evaluating payment risk..."
                      : "Evaluate payment risk"}

                    <span>→</span>
                  </button>

                  <p className="disclaimer">
                    VeriPay evaluates risk only. It does not
                    initiate or authorize a UPI payment.
                  </p>
                </form>
              </article>

              <div className="right-column">
                <article className="panel decision-panel">
                  <div className="panel-heading">
                    <div className="panel-icon">◎</div>

                    <div>
                      <h3>Risk decision</h3>

                      <p>
                        CPDE assessment and recommended action.
                      </p>
                    </div>
                  </div>

                  {!result && !loading && (
                    <div className="empty-state">
                      <div className="empty-illustration">
                        <div className="empty-shield">✓</div>
                      </div>

                      <span className="card-overline">
                        AWAITING ASSESSMENT
                      </span>

                      <h3>Your decision will appear here.</h3>

                      <p>
                        Complete the payment details and evaluate
                        the transaction to view its risk level
                        and recommended action.
                      </p>
                    </div>
                  )}

                  {loading && (
                    <div className="loading-state">
                      <div className="loader-ring" />

                      <h3>Evaluating transaction</h3>

                      <p>
                        Analysing contextual risk signals...
                      </p>
                    </div>
                  )}

                  {result && (
                    <div className="result-content">
                      <div className={`risk-banner ${riskClass}`}>
                        <div className="risk-symbol">
                          {risk === "HIGH"
                            ? "!"
                            : risk === "MEDIUM"
                              ? "◇"
                              : "✓"}
                        </div>

                        <div>
                          <span className="card-overline">
                            ASSESSED RISK
                          </span>

                          <h2>{risk || "UNKNOWN"} RISK</h2>

                          <p>
                            {result.reason ||
                              "Review the decision details."}
                          </p>
                        </div>
                      </div>

                      <div className="transaction-summary">
                        <div>
                          <span>RECIPIENT</span>

                          <strong>
                            {form.recipient || "Not specified"}
                          </strong>
                        </div>

                        <div>
                          <span>PAYMENT AMOUNT</span>

                          <strong>
                            ₹{formatAmount(form.amount)}
                          </strong>
                        </div>
                      </div>

                      <div className="metric-grid">
                        <div className="metric">
                          <span>Fraud probability</span>

                          <strong>
                            {Number.isFinite(
                              Number(result.fraud_probability)
                            )
                              ? `${(
                                Number(
                                  result.fraud_probability
                                ) * 100
                              ).toFixed(2)}%`
                              : "N/A"}
                          </strong>
                        </div>

                        <div className="metric">
                          <span>Context risk score</span>

                          <strong>
                            {Number.isFinite(
                              Number(result.context_score)
                            )
                              ? `${(
                                Number(result.context_score) *
                                100
                              ).toFixed(1)}%`
                              : "N/A"}
                          </strong>
                        </div>
                      </div>

                      <div className="signals-heading">
                        <h4>Contextual risk signals</h4>
                        <span>CPDE ANALYSIS</span>
                      </div>

                      <div className="signal-list">
                        {Object.entries(
                          result.context_signals || {}
                        ).map(([key, value]) => (
                          <div className="signal-row" key={key}>
                            <span>
                              {key.replaceAll("_", " ")}
                            </span>

                            <strong>
                              {Number.isFinite(Number(value))
                                ? Number(value).toFixed(2)
                                : String(value)}
                            </strong>
                          </div>
                        ))}

                        {!Object.keys(
                          result.context_signals || {}
                        ).length && (
                            <p className="no-signals">
                              No contextual signals returned.
                            </p>
                          )}
                      </div>

                      <div className="decision-box">
                        <span>RECOMMENDED ACTION</span>

                        <strong>{decision}</strong>

                        <p>
                          {result.payment_decision ||
                            "Review the assessment."}
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
                          Explicit confirmation is required
                          before any future payment workflow
                          could proceed.
                        </p>
                      )}
                    </div>
                  )}
                </article>

                <article className="panel safety-note">
                  <div className="panel-icon">✳</div>

                  <div>
                    <h3>Safety by design</h3>

                    <p>
                      Every result is an assessment
                      recommendation. No money is transferred
                      by this prototype.
                    </p>
                  </div>
                </article>
              </div>
            </section>
          </div>
        )}

        {activePage === "security" && (
          <div className="page security-page">
            <section className="page-intro">
              <span className="eyebrow">
                TRANSACTION PROTECTION
              </span>

              <h1>
                Security <span>insights.</span>
              </h1>

              <p>
                Understand how VeriPay evaluates contextual
                signals to identify potentially risky payment
                behaviour.
              </p>
            </section>

            <section className="security-grid">
              <article className="panel security-card">
                <div className="security-card-icon">⌁</div>

                <span className="card-overline">
                  SIGNAL 01
                </span>

                <h3>Recipient familiarity</h3>

                <p>
                  Checks whether the recipient is known or
                  unfamiliar, helping identify payments to
                  potentially suspicious recipients.
                </p>
              </article>

              <article className="panel security-card">
                <div className="security-card-icon">₹</div>

                <span className="card-overline">
                  SIGNAL 02
                </span>

                <h3>Amount deviation</h3>

                <p>
                  Compares the current transaction amount
                  against the user's typical payment behaviour.
                </p>
              </article>

              <article className="panel security-card">
                <div className="security-card-icon">◉</div>

                <span className="card-overline">
                  SIGNAL 03
                </span>

                <h3>Voice intent confidence</h3>

                <p>
                  Evaluates how confidently the spoken command
                  can be interpreted as a payment instruction.
                </p>
              </article>

              <article className="panel security-card">
                <div className="security-card-icon">◇</div>

                <span className="card-overline">
                  SIGNAL 04
                </span>

                <h3>Recipient ambiguity</h3>

                <p>
                  Helps identify situations where a spoken
                  recipient name may match multiple contacts.
                </p>
              </article>

              <article className="panel security-card">
                <div className="security-card-icon">◎</div>

                <span className="card-overline">
                  SIGNAL 05
                </span>

                <h3>Transaction risk</h3>

                <p>
                  Uses transaction-related features to estimate
                  the possibility of fraudulent behaviour.
                </p>
              </article>

              <article className="panel security-card">
                <div className="security-card-icon">✓</div>

                <span className="card-overline">
                  DECISION LAYER
                </span>

                <h3>Explainable decisions</h3>

                <p>
                  Combines contextual signals to generate
                  understandable recommendations such as
                  PROCEED, WARN or BLOCK.
                </p>
              </article>
            </section>

            <article className="panel security-footer-panel">
              <div className="security-footer-icon">✳</div>

              <div>
                <h3>Designed around user safety</h3>

                <p>
                  VeriPay is a research prototype. It evaluates
                  payment risk and does not execute actual UPI
                  transactions.
                </p>
              </div>
            </article>
          </div>
        )}

        <footer className="footer">
          <span>
            VeriPay <i>·</i> Context-Aware Payment Decision Engine
          </span>

          <span>
            Research prototype <i>·</i> No live payment integration
          </span>
        </footer>
      </main>
    </div>
  );
}

export default App;