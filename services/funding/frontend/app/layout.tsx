import type { Metadata } from 'next'
import React from "react";
import {AppContainer} from "@/app/app";

import './globals.css'
import 'react-toastify/dist/ReactToastify.css';
import {ToastContainer} from "react-toastify";

export const metadata: Metadata = {
  title: 'Crowdfunding',
  description: 'Web3 Crowdfunding Platform',
}

export default function RootLayout({children}: {children: React.ReactNode}) {
  return (
    <html lang="en">
      <body>
        <ToastContainer/>
        <AppContainer>
          {children}
        </AppContainer>
      </body>
    </html>
  )
}
