import { DataItem } from '../types';

// API 基础地址 - 默认指向本地后端
const API_BASE = 'http://localhost:8000';

export const fetchTotalCount = async (): Promise<number> => {
    const response = await fetch(`${API_BASE}/count`);
    if (!response.ok) {
        throw new Error('Failed to fetch count');
    }
    const data = await response.json();
    return data.total;
};

export const fetchDataByIndex = async (index: number): Promise<DataItem | null> => {
    const response = await fetch(`${API_BASE}/data/${index}`);
    if (!response.ok) {
        if (response.status === 404) {
            return null;
        }
        throw new Error(`Failed to fetch data at index ${index}`);
    }
    return response.json();
};