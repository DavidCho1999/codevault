"use client";

import { useState, useMemo } from "react";
import tablesData from "../../../public/data/part9_tables_v9_fixed.json";

interface TableEntry {
  page: number;
  index: number;
  table_id: string | null;
  unique_id?: string;
  source: string;
  accuracy: number;
  rows: number;
  cols: number;
  headers: (string | null)[];
  data: (string | null)[][];
  raw_data: (string | null)[][];
  pages?: number[];
  start_page?: number;
  end_page?: number;
}

const tables = tablesData as TableEntry[];

function TableRenderer({ table }: { table: TableEntry }) {
  const { raw_data, table_id, page, source, accuracy, rows, cols, pages } = table;

  const pageDisplay = pages && pages.length > 1
    ? `Pages ${pages[0]}-${pages[pages.length - 1]}`
    : `Page ${page}`;

  return (
    <div className="border border-gray-200 rounded-lg overflow-hidden bg-white">
      {/* Header */}
      <div className="bg-gray-50 px-4 py-3 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="font-semibold text-gray-900">
              {table_id ? `Table ${table_id}` : `Table (Page ${page})`}
              {pages && pages.length > 1 && (
                <span className="ml-2 text-xs text-orange-600">
                  ({pages.length} pages)
                </span>
              )}
            </h3>
            <p className="text-sm text-gray-500">
              {rows} rows × {cols} cols | {pageDisplay}
            </p>
          </div>
          <div className="text-right">
            <span className={`inline-block px-2 py-1 text-xs rounded ${
              source === 'camelot-lattice'
                ? 'bg-green-100 text-green-800'
                : 'bg-blue-100 text-blue-800'
            }`}>
              {source}
            </span>
            {accuracy > 0 && (
              <p className="text-xs text-gray-400 mt-1">
                {accuracy.toFixed(1)}% accuracy
              </p>
            )}
          </div>
        </div>
      </div>

      {/* Table Content */}
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-100">
            {raw_data.slice(0, 1).map((row, rowIdx) => (
              <tr key={rowIdx}>
                {row.map((cell, cellIdx) => (
                  <th
                    key={cellIdx}
                    className="px-3 py-2 text-left text-xs font-medium text-gray-700 uppercase tracking-wider border-r border-gray-200 last:border-r-0"
                  >
                    {cell || "-"}
                  </th>
                ))}
              </tr>
            ))}
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {raw_data.slice(1).map((row, rowIdx) => (
              <tr key={rowIdx} className={rowIdx % 2 === 0 ? "bg-white" : "bg-gray-50"}>
                {row.map((cell, cellIdx) => (
                  <td
                    key={cellIdx}
                    className="px-3 py-2 text-sm text-gray-700 border-r border-gray-100 last:border-r-0"
                  >
                    {cell || <span className="text-gray-300">-</span>}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default function TablesPage() {
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedPage, setSelectedPage] = useState<number | null>(null);

  // Get unique pages for filter
  const uniquePages = useMemo(() => {
    const pages = [...new Set(tables.map((t) => t.page))].sort((a, b) => a - b);
    return pages;
  }, []);

  // Filter tables
  const filteredTables = useMemo(() => {
    return tables.filter((table) => {
      const matchesSearch =
        !searchQuery ||
        (table.table_id && table.table_id.toLowerCase().includes(searchQuery.toLowerCase())) ||
        table.raw_data.some((row) =>
          row.some((cell) => cell && cell.toLowerCase().includes(searchQuery.toLowerCase()))
        );

      const matchesPage = selectedPage === null || table.page === selectedPage;

      return matchesSearch && matchesPage;
    });
  }, [searchQuery, selectedPage]);

  // Stats
  const stats = useMemo(() => {
    return {
      total: tables.length,
      withId: tables.filter((t) => t.table_id).length,
      multiPage: tables.filter((t) => t.pages && t.pages.length > 1).length,
      totalRows: tables.reduce((sum, t) => sum + t.rows, 0),
    };
  }, []);

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          Part 9 Tables
        </h1>
        <p className="text-gray-600">
          Ontario Building Code 2024 - Extracted Tables
        </p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        <div className="bg-white p-4 rounded-lg border border-gray-200">
          <p className="text-2xl font-bold text-blue-600">{stats.total}</p>
          <p className="text-sm text-gray-500">Total Tables</p>
        </div>
        <div className="bg-white p-4 rounded-lg border border-gray-200">
          <p className="text-2xl font-bold text-green-600">{stats.withId}</p>
          <p className="text-sm text-gray-500">With Table ID</p>
        </div>
        <div className="bg-white p-4 rounded-lg border border-gray-200">
          <p className="text-2xl font-bold text-purple-600">{stats.multiPage}</p>
          <p className="text-sm text-gray-500">Multi-page Tables</p>
        </div>
        <div className="bg-white p-4 rounded-lg border border-gray-200">
          <p className="text-2xl font-bold text-orange-600">{stats.totalRows}</p>
          <p className="text-sm text-gray-500">Total Rows</p>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white p-4 rounded-lg border border-gray-200 mb-6">
        <div className="flex gap-4">
          <div className="flex-1">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Search
            </label>
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search by table ID or content..."
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
          <div className="w-48">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Page
            </label>
            <select
              value={selectedPage ?? ""}
              onChange={(e) =>
                setSelectedPage(e.target.value ? Number(e.target.value) : null)
              }
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="">All Pages</option>
              {uniquePages.map((page) => (
                <option key={page} value={page}>
                  Page {page}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Results count */}
      <p className="text-sm text-gray-500 mb-4">
        Showing {filteredTables.length} of {tables.length} tables
      </p>

      {/* Tables Grid */}
      <div className="space-y-6">
        {filteredTables.map((table, idx) => (
          <TableRenderer key={`${table.page}-${table.index}-${idx}`} table={table} />
        ))}
      </div>

      {filteredTables.length === 0 && (
        <div className="text-center py-12 text-gray-500">
          No tables found matching your criteria.
        </div>
      )}
    </div>
  );
}
