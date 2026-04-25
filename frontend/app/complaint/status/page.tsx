"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";
import { ComplaintStatus, getComplaintStatus } from "@/lib/api";

export default function ComplaintStatusPage() {
  const [token, setToken] = useState("");
  const [status, setStatus] = useState<ComplaintStatus | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setError(null);
    setStatus(null);

    try {
      const result = await getComplaintStatus(token.trim());
      setStatus(result);
    } catch (err) {
      console.error("Complaint status error:", err);
      setError(err instanceof Error ? err.message : "Unable to check complaint status.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="flex min-h-screen flex-col items-center justify-center bg-gray-50 px-4">
      <div className="w-full max-w-xl">
        <Link href="/complaint" className="text-sm font-medium text-blue-600 hover:text-blue-800">
          ← Back to complaint form
        </Link>
        <div className="mt-4 rounded-xl bg-white p-6 shadow">
          <h1 className="text-2xl font-bold text-gray-900">Check Complaint Status</h1>
          <p className="mt-2 text-gray-600">
            Enter the anonymous token you received after filing a complaint.
          </p>

          <form onSubmit={handleSubmit} className="mt-6 flex flex-col gap-4">
            <label className="flex flex-col">
              <span className="mb-1 font-medium text-gray-800">Complaint token</span>
              <input
                value={token}
                onChange={(event) => setToken(event.target.value)}
                required
                className="rounded-lg border px-3 py-2 font-mono text-sm text-gray-900 focus:ring-2 focus:ring-blue-500"
                placeholder="Paste your complaint token"
              />
            </label>
            <button
              type="submit"
              disabled={loading}
              className="rounded-lg bg-blue-600 px-6 py-2.5 font-semibold text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {loading ? "Checking..." : "Check Status"}
            </button>
          </form>

          {error && (
            <div className="mt-4 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">
              {error}
            </div>
          )}

          {status && (
            <div className="mt-4 rounded-lg border bg-gray-50 p-4">
              <p className="text-sm text-gray-600">Status</p>
              <p className="mt-1 text-lg font-semibold capitalize text-gray-900">{status.status}</p>
              <p className="mt-3 text-sm text-gray-600">Agency</p>
              <p className="text-gray-900">{status.agency}</p>
            </div>
          )}
        </div>
      </div>
    </main>
  );
}
