// src/types.ts

type Nullable<T> = T | null;
type Optional<T> = T | undefined;

interface BaseProps {
  className?: string;
  style?: React.CSSProperties;
  children?: React.ReactNode;
}

interface PatientRecord {
  id: string;
  name: string;
  medicalHistory: string[];
  insuranceClaims: string[];
  // Add other properties as needed
}

interface HealthcareContextProps {
  patientRecords: Nullable<PatientRecord[]>;
  getPatientRecord: (id: string) => Promise<Nullable<PatientRecord>>;
  savePatientRecord: (record: PatientRecord) => Promise<void>;
  deletePatientRecord: (id: string) => Promise<void>;
  // Add other methods as needed
}