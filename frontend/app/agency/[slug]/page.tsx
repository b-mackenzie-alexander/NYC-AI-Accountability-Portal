"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { AgencyDetail, getAgencyDetail } from "@/lib/api";

export default function AgencyOverviewPage() {
  const params = useParams<{ slug: string }>();
  const [agency, setAgency] = useState<AgencyDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;

    async function loadAgency() {
      try {
        setLoading(true);
        setError(null);
        const detail = await getAgencyDetail(params.slug);
        if (!active) return;
        setAgency(detail);
      } catch (err) {
        if (!active) return;
        console.error("Agency detail error:", err);
        setError(err instanceof Error ? err.message : "Unable to load agency detail.");
      } finally {
        if (active) setLoading(false);
      }
    }

    loadAgency();
    return () => {
      active = false;
    };
  }, [params.slug]);

  return (
    <main className="min-h-screen bg-gray-50 px-4 py-12">
      <div className="mx-auto w-full max-w-4xl">
        <Link href="/agencies" className="text-sm font-medium text-blue-600 hover:text-blue-800">
          ← Back to agencies
        </Link>

        {loading ? (
          <div className="mt-10 rounded-xl bg-white p-10 text-center text-gray-500 shadow">
            <div className="mb-4 inline-block h-8 w-8 animate-spin rounded-full border-b-2 border-blue-600"></div>
            <p>Loading agency overview...</p>
          </div>
        ) : error ? (
          <div className="mt-10 rounded-xl border border-red-200 bg-red-50 p-6 text-red-700">
            {error}
          </div>
        ) : agency ? (
          <>
            <section className="mt-6 rounded-xl bg-white p-6 shadow">
              <p className="mb-2 text-sm font-semibold uppercase tracking-wide text-blue-600">
                Agency Overview
              </p>
              <h1 className="text-3xl font-bold text-gray-900">{agency.name}</h1>
              <p className="mt-2 text-gray-600">{agency.description}</p>
              <div className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-3">
                <div className="rounded-lg border p-4">
                  <div className="text-2xl font-bold text-gray-900">{agency.disclosed_systems_count}</div>
                  <div className="text-sm text-gray-600">Disclosed systems</div>
                </div>
                <div className="rounded-lg border p-4">
                  <div className="text-2xl font-bold text-gray-900">{agency.active_signals_count}</div>
                  <div className="text-sm text-gray-600">Active signals</div>
                </div>
                <div className="rounded-lg border p-4">
                  <div className="text-2xl font-bold capitalize text-gray-900">
                    {agency.highest_severity || "None"}
                  </div>
                  <div className="text-sm text-gray-600">Highest severity</div>
                </div>
              </div>
            </section>

            <section className="mt-6 rounded-xl bg-white p-6 shadow">
              <h2 className="text-xl font-semibold text-gray-900">AI System Disclosures</h2>
              {agency.disclosures.length === 0 ? (
                <p className="mt-4 text-gray-500">No disclosures are currently listed for this agency.</p>
              ) : (
                <ul className="mt-4 divide-y divide-gray-200">
                  {agency.disclosures.map((disclosure, index) => (
                    <li key={disclosure.id || `${disclosure.system_name}-${index}`} className="py-4">
                      <h3 className="font-semibold text-gray-900">{disclosure.system_name}</h3>
                      <p className="mt-1 text-sm text-gray-600">
                        {disclosure.purpose || "Purpose not disclosed."}
                      </p>
                      {disclosure.vendor && (
                        <p className="mt-1 text-xs text-gray-500">Vendor: {disclosure.vendor}</p>
                      )}
                    </li>
                  ))}
                </ul>
              )}
            </section>

            <section className="mt-6 rounded-xl bg-white p-6 shadow">
              <h2 className="text-xl font-semibold text-gray-900">Bias Signals</h2>
              {agency.signals.length === 0 ? (
                <p className="mt-4 text-gray-500">No active bias signals are currently listed.</p>
              ) : (
                <ul className="mt-4 divide-y divide-gray-200">
                  {agency.signals.map((signal, index) => (
                    <li key={signal.id || `${signal.signal_type}-${index}`} className="py-4">
                      <div className="flex items-center gap-2">
                        <h3 className="font-semibold text-gray-900">{signal.signal_type}</h3>
                        <span className="rounded-full bg-orange-100 px-2 py-0.5 text-xs font-medium uppercase text-orange-800">
                          {signal.severity}
                        </span>
                      </div>
                      <p className="mt-1 text-sm text-gray-600">
                        {signal.description || "No additional description supplied."}
                      </p>
                    </li>
                  ))}
                </ul>
              )}
            </section>
          </>
        ) : (
          <div className="mt-10 rounded-xl bg-white p-6 text-gray-700 shadow">
            We could not find that agency in the current demo directory.
          </div>
        )}
      </div>
    </main>
  );
}
