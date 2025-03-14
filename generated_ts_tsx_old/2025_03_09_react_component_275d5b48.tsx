import React, { createContext, useContext, useState, useEffect } from 'react';

type Nullable<T> = T | null;

interface ApiResponse<T> {
    data: T;
    status: number;
    message: string;
}

interface AppContextType {
    routeData: ApiResponse<string> | null;
    setRouteData: (data: ApiResponse<string> | null) => void;
}

const AppContext = createContext<AppContextType>({
    routeData: null,
    setRouteData: () => {},
});

export const useAppContext = () => useContext(AppContext);

export const AppProvider: React.FC<BaseProps> = ({ children }) => {
    const [routeData, setRouteData] = useState<ApiResponse<string> | null>(null);

    useEffect(() => {
        // Simulate fetching route data
        const fetchData = async () => {
            const response = await fetch('/api/route');
            const data = await response.json();
            setRouteData(data);
        };

        fetchData();

        return () => {
            // Cleanup logic here if needed
        };
    }, []);

    return (
        <AppContext.Provider value={{ routeData, setRouteData }}>
            {children}
        </AppContext.Provider>
    );
};

interface BaseProps {
    className?: string;
    style?: React.CSSProperties;
    children?: React.ReactNode;
}