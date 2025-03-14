// Import necessary dependencies
import React, { createContext, useContext, useState, useEffect } from 'react';
import axios from 'axios';
import { v4 as uuidv4 } from 'uuid';
import mongoose from 'mongoose';
import { useAuth } from './AuthContext'; // Assuming you have an AuthContext for authentication

// Utility Types and Interfaces
type Nullable<T> = T | null;

interface ApiResponse<T> {
    data: T;
    status: number;
    message: string;
}

// Error Handling Service
interface ErrorHandlingService {
    handleError: (error: any) => void;
}

const ErrorHandlingContext = createContext<Nullable<ErrorHandlingService>>(null);

const ErrorHandlingProvider: React.FC = ({ children }) => {
    const handleError = (error: any) => {
        console.error('Error occurred:', error);
        // Log the error to a monitoring service (e.g., Sentry)
        // Sentry.captureException(error);
    };

    return (
        <ErrorHandlingContext.Provider value={{ handleError }}>
            {children}
        </ErrorHandlingContext.Provider>
    );
};

const useErrorHandling = () => {
    const context = useContext(ErrorHandlingContext);
    if (context === null) {
        throw new Error('useErrorHandling must be used within an ErrorHandlingProvider');
    }
    return context;
};

// Authentication Service
interface AuthService {
    isAuthenticated: boolean;
    login: (username: string, password: string) => Promise<ApiResponse<boolean>>;
    logout: () => void;
}

const AuthContext = createContext<Nullable<AuthService>>(null);

const AuthProvider: React.FC = ({ children }) => {
    const [isAuthenticated, setIsAuthenticated] = useState(false);

    const login = async (username: string, password: string): Promise<ApiResponse<boolean>> => {
        try {
            const response = await axios.post('/api/login', { username, password });
            setIsAuthenticated(true);
            return { data: true, status: response.status, message: 'Login successful' };
        } catch (error) {
            return { data: false, status: error.response?.status || 500, message: error.response?.data || 'Login failed' };
        }
    };

    const logout = () => {
        setIsAuthenticated(false);
        // Clear any authentication tokens or cookies
    };

    return (
        <AuthContext.Provider value={{ isAuthenticated, login, logout }}>
            {children}
        </AuthContext.Provider>
    );
};

const useAuth = () => {
    const context = useContext(AuthContext);
    if (context === null) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
};

// Patient Record Service
interface PatientRecord {
    id: string;
    name: string;
    medicalHistory: string;
    insuranceClaims: string[];
}

interface PatientRecordService {
    fetchPatientRecords: () => Promise<ApiResponse<PatientRecord[]>>;
    createPatientRecord: (record: PatientRecord) => Promise<ApiResponse<PatientRecord>>;
    updatePatientRecord: (record: PatientRecord) => Promise<ApiResponse<PatientRecord>>;
    deletePatientRecord: (id: string) => Promise<ApiResponse<boolean>>;
}

const PatientRecordContext = createContext<Nullable<PatientRecordService>>(null);

const PatientRecordProvider: React.FC = ({ children }) => {
    const { handleError } = useErrorHandling();
    const { isAuthenticated } = useAuth();

    const fetchPatientRecords = async (): Promise<ApiResponse<PatientRecord[]>> => {
        if (!isAuthenticated) {
            return { data: [], status: 401, message: 'Not authenticated' };
        }

        try {
            const response = await axios.get('/api/patient-records');
            return { data: response.data, status: response.status, message: 'Patient records fetched successfully' };
        } catch (error) {
            handleError(error);
            return { data: [], status: error.response?.status || 500, message: error.response?.data || 'Failed to fetch patient records' };
        }
    };

    const createPatientRecord = async (record: PatientRecord): Promise<ApiResponse<PatientRecord>> => {
        if (!isAuthenticated) {
            return { data: null, status: 401, message: 'Not authenticated' };
        }

        try {
            const response = await axios.post('/api/patient-records', record);
            return { data: response.data, status: response.status, message: 'Patient record created successfully' };
        } catch (error) {
            handleError(error);
            return { data: null, status: error.response?.status || 500, message: error.response?.data || 'Failed to create patient record' };
        }
    };

    const updatePatientRecord = async (record: PatientRecord): Promise<ApiResponse<PatientRecord>> => {
        if (!isAuthenticated) {
            return { data: null, status: 401, message: 'Not authenticated' };
        }

        try {
            const response = await axios.put(`/api/patient-records/${record.id}`, record);
            return { data: response.data, status: response.status, message: 'Patient record updated successfully' };
        } catch (error) {
            handleError(error);
            return { data: null, status: error.response?.status || 500, message: error.response?.data || 'Failed to update patient record' };
        }
    };

    const deletePatientRecord = async (id: string): Promise<ApiResponse<boolean>> => {
        if (!isAuthenticated) {
            return { data: false, status: 401, message: 'Not authenticated' };
        }

        try {
            const response = await axios.delete(`/api/patient-records/${id}`);
            return { data: true, status: response.status, message: 'Patient record deleted successfully' };
        } catch (error) {
            handleError(error);
            return { data: false, status: error.response?.status || 500, message: error.response?.data || 'Failed to delete patient record' };
        }
    };

    return (
        <PatientRecordContext.Provider value={{ fetchPatientRecords, createPatientRecord, updatePatientRecord, deletePatientRecord }}>
            {children}
        </PatientRecordContext.Provider>
    );
};

const usePatientRecord = () => {
    const context = useContext(PatientRecordContext);
    if (context === null) {
        throw new Error('usePatientRecord must be used within a PatientRecordProvider');
    }
    return context;
};

// MongoDB with Mongoose for Transaction and Archive
const patientRecordSchema = new mongoose.Schema<PatientRecord>({
    id: { type: String, default: uuidv4 },
    name: String,
    medicalHistory: String,
    insuranceClaims: [String]
});

const PatientRecord = mongoose.model<PatientRecord>('PatientRecord', patientRecordSchema);

const archiveOldRecords = async (threshold: number) => {
    try {
        const session = await mongoose.startSession();
        session.startTransaction();

        const oldRecords = await PatientRecord.find({}).where('createdAt').lt(new Date(Date.now() - threshold)).session(session);

        if (oldRecords.length > 0) {
            await PatientRecord.deleteMany({ _id: { $in: oldRecords.map(record => record.id) } }).session(session);
            await session.commitTransaction();
            console.log('Old records archived successfully');
        } else {
            console.log('No old records to archive');
        }

        session.endSession();
    } catch (error) {
        console.error('Error archiving old records:', error);
        // Handle transaction rollback
        await mongoose.connection.transaction(async (session) => {
            await session.abortTransaction();
        });
    }
};

// Example Usage
const App: React.FC = () => {
    const { login, logout, isAuthenticated } = useAuth();
    const { fetchPatientRecords, createPatientRecord, updatePatientRecord, deletePatientRecord } = usePatientRecord();
    const [patientRecords, setPatientRecords] = useState<PatientRecord[]>([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const fetchRecords = async () => {
            setLoading(true);
            try {
                const response = await fetchPatientRecords();
                if (response.status === 200) {
                    setPatientRecords(response.data);
                } else {
                    setError(response.message);
                }
            } catch (error) {
                setError('Failed to fetch patient records');
            } finally {
                setLoading(false);
            }
        };

        fetchRecords();
    }, [fetchPatientRecords]);

    const handleCreateRecord = async (record: PatientRecord) => {
        try {
            const response = await createPatientRecord(record);
            if (response.status === 200) {
                setPatientRecords([...patientRecords, response.data]);
            } else {
                setError(response.message);
            }
        } catch (error) {
            setError('Failed to create patient record');
        }
    };

    const handleUpdateRecord = async (record: PatientRecord) => {
        try {
            const response = await updatePatientRecord(record);
            if (response.status === 200) {
                setPatientRecords(patientRecords.map(r => (r.id === record.id ? response.data : r)));
            } else {
                setError(response.message);
            }
        } catch (error) {
            setError('Failed to update patient record');
        }
    };

    const handleDeleteRecord = async (id: string) => {
        try {
            const response = await deletePatientRecord(id);
            if (response.status === 200) {
                setPatientRecords(patientRecords.filter(r => r.id !== id));
            } else {
                setError(response.message);
            }
        } catch (error) {
            setError('Failed to delete patient record');
        }
    };

    return (
        <div>
            <h1>Healthcare Platform</h1>
            {isAuthenticated ? (
                <div>
                    <button onClick={logout}>Logout</button>
                    <h2>Patient Records</h2>
                    {loading ? (
                        <p>Loading...</p>
                    ) : error ? (
                        <p>{error}</p>
                    ) : (
                        <ul>
                            {patientRecords.map(record => (
                                <li key={record.id}>
                                    {record.name} - {record.medicalHistory}
                                    <button onClick={() => handleDeleteRecord(record.id)}>Delete</button>
                                    <button onClick={() => handleUpdateRecord(record)}>Update</button>
                                </li>
                            ))}
                        </ul>
                    )}
                    <button onClick={() => handleCreateRecord({ id: uuidv4(), name: 'John Doe', medicalHistory: 'Diabetes', insuranceClaims: ['Claim1', 'Claim2'] })}>
                        Create Record
                    </button>
                </div>
            ) : (
                <button onClick={() => login('user', 'password')}>Login</button>
            )}
        </div>
    );
};

// Root Component
const HealthcareApp: React.FC = () => {
    return (
        <ErrorHandlingProvider>
            <AuthProvider>
                <PatientRecordProvider>
                    <App />
                </PatientRecordProvider>
            </AuthProvider>
        </ErrorHandlingProvider>
    );
};

export default HealthcareApp;