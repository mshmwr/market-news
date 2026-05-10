// Firestore client init for feedback submissions.
// Same project as docs/index.html legacy build (ai-novel-generator-ng / feedback collection).

import { initializeApp, getApps, type FirebaseApp } from 'firebase/app';
import { getFirestore, type Firestore } from 'firebase/firestore';

const config = {
  apiKey: 'AIzaSyA3QVtTSwTSXaMA_AbsQ863xB475OcbdmA',
  authDomain: 'ai-novel-generator-ng.firebaseapp.com',
  projectId: 'ai-novel-generator-ng',
  storageBucket: 'ai-novel-generator-ng.firebasestorage.app',
  messagingSenderId: '603430013176',
  appId: '1:603430013176:web:20f79a5819c32c689dd30d',
};

let _db: Firestore | null = null;

export function getDb(): Firestore {
  if (_db) return _db;
  const app: FirebaseApp = getApps()[0] ?? initializeApp(config);
  _db = getFirestore(app);
  return _db;
}
