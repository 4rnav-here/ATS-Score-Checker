import type { Metadata } from "next";
import NoiseOverlay from "./components/NoiseOverlay";
import "./globals.css";

export const metadata: Metadata = {
  title: "ATS Analyzer | Superdesign",
  description: "AI-powered resume ATS scoring engine",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="h-full antialiased">
      <head>
        <link href="https://api.fontshare.com/v2/css?f[]=clash-grotesk@200,300,400,500,600,700&f[]=general-sans@200,300,400,500,600,700&display=swap" rel="stylesheet" />
      </head>
      <body className="min-h-full flex flex-col font-sans selection:bg-accent selection:text-background relative">
        <NoiseOverlay />
        {children}
      </body>
    </html>
  );
}
