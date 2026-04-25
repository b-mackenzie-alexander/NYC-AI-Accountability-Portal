import { notFound } from "next/navigation";
import UploadDemoClient from "./UploadDemoClient";

export default function AdminUploadPage() {
  if (process.env.ADMIN_UPLOAD_DEMO_ENABLED !== "true") {
    notFound();
  }

  return <UploadDemoClient />;
}
