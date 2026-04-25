import { afterEach, describe, expect, it, vi } from "vitest";
import {
  getAgencySummaries,
  submitComplaint,
  uploadDisclosure,
} from "../lib/api";

const fetchMock = vi.fn();

global.fetch = fetchMock;

function jsonResponse(body: unknown, init: ResponseInit = {}) {
  return new Response(JSON.stringify(body), {
    status: init.status ?? 200,
    headers: { "Content-Type": "application/json" },
  });
}

afterEach(() => {
  fetchMock.mockReset();
});

describe("api helpers", () => {
  it("returns the backend complaint_token from complaint submissions", async () => {
    fetchMock.mockResolvedValueOnce(
      jsonResponse({
        status: "received",
        complaint_token: "token-123",
        message: "Save this token.",
      }),
    );

    const result = await submitComplaint({
      agency: "ACS",
      incident_description: "A decision used an automated score.",
    });

    expect(result.complaint_token).toBe("token-123");
    expect(fetchMock).toHaveBeenCalledWith(
      "http://localhost:8000/complaints",
      expect.objectContaining({ method: "POST" }),
    );
  });

  it("throws API detail text for non-OK responses", async () => {
    fetchMock.mockResolvedValueOnce(jsonResponse({ detail: "Rate limit exceeded." }, { status: 429 }));

    await expect(
      submitComplaint({
        agency: "ACS",
        incident_description: "A decision used an automated score.",
      }),
    ).rejects.toThrow("Rate limit exceeded.");
  });

  it("aggregates agency summaries from disclosures and signals", async () => {
    fetchMock
      .mockResolvedValueOnce(
        jsonResponse([
          { agency_name: "Administration for Children's Services", system_name: "Family Map" },
          { agency_name: "ACS", system_name: "Risk Model" },
          { agency_name: "NYPD", system_name: "Domain Awareness System" },
        ]),
      )
      .mockResolvedValueOnce(
        jsonResponse([
          { agency: "ACS", signal_type: "disclosure_gap", severity: "medium" },
          { agency: "NY Police Department", signal_type: "bias_audit_gap", severity: "high" },
        ]),
      );

    const agencies = await getAgencySummaries();
    const acs = agencies.find((agency) => agency.id === "acs");
    const nypd = agencies.find((agency) => agency.id === "nypd");

    expect(acs).toMatchObject({
      disclosed_systems_count: 2,
      active_signals_count: 1,
      highest_severity: "medium",
    });
    expect(nypd).toMatchObject({
      disclosed_systems_count: 1,
      active_signals_count: 1,
      highest_severity: "high",
    });
  });

  it("uploads disclosures as multipart data with the admin token header", async () => {
    fetchMock.mockResolvedValueOnce(jsonResponse({ stored: 1 }));
    const file = new File(["pdf bytes"], "disclosure.pdf", { type: "application/pdf" });

    await uploadDisclosure(file, "ACS", "secret-token");

    const [, init] = fetchMock.mock.calls[0];
    expect(fetchMock).toHaveBeenCalledWith(
      "http://localhost:8000/disclosures/upload",
      expect.objectContaining({ method: "POST" }),
    );
    expect(init.headers).toEqual({ "X-Admin-Token": "secret-token" });
    expect(init.body).toBeInstanceOf(FormData);
    expect((init.body as FormData).get("agency_name")).toBe("ACS");
    expect((init.body as FormData).get("file")).toBe(file);
  });
});
