import { useEffect, useState } from "react";
import "./VeriPayLoader.css";

export default function VeriPayLoader() {
    const [visible, setVisible] = useState(true);
    const [exiting, setExiting] = useState(false);

    useEffect(() => {
        const exitTimer = setTimeout(() => setExiting(true), 1600);
        const hideTimer = setTimeout(() => setVisible(false), 2100);

        return () => {
            clearTimeout(exitTimer);
            clearTimeout(hideTimer);
        };
    }, []);

    if (!visible) return null;

    return (
        <div className={`veripay-loader ${exiting ? "loader-exit" : ""}`}>
            <div className="loader-content">
                <div className="loader-logo">
                    <div className="loader-orbit">
                        <span className="loader-v">V</span>
                    </div>
                </div>

                <h1 className="loader-title">
                    Veri<span>Pay</span>
                </h1>

                <p className="loader-subtitle">
                    Intelligent payments. Trusted decisions.
                </p>

                <div className="loader-spinner"></div>

                <p className="loader-status">Securing your payment experience</p>

                <div className="loader-security">
                    <span>✦</span> AI-powered security
                </div>
            </div>
        </div>
    );
}