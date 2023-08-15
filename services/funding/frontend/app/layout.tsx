import type { Metadata } from 'next'
import React from "react";
import { AppContainer } from "@/app/app";
import { ToastContainer } from "react-toastify";

import './globals.css'
import 'react-toastify/dist/ReactToastify.css';

export const metadata: Metadata = {
  title: 'Crowdfunding',
  description: 'Web3 Crowdfunding Platform',
}

export default function RootLayout({children}: {children: React.ReactNode}) {
  return (
    <html lang="en">
      <body>
        <ToastContainer style={{ width: "500px" }}/>
        <AppContainer>
          {children}
        </AppContainer>
      </body>
    </html>
  )
}
