"use client";

import React, { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import {
  ChevronRight,
  Flag,
  Check,
  Trash2,
  Eye,
  AlertCircle,
  Loader2,
} from "lucide-react";
import Link from "next/link";
import Toast, { ToastType } from "@/components/ui/Toast";
import { getReports, deleteCommentAsAdmin, updateReportStatus,deleteReport } from "@/lib/reportsApi";

interface Report {
  report_id: string;
  restaurant_id: string;
  comment_id: string;
  comment_text: string;
  reason: string;
  status: "pending" | "resolved";
  created_at: string;
  reporter_user_id?: string;
  restaurant_name?: string;
  type_resolve: "deleted" | "dismissed" | null;
}

export default function AdminPage() {
  const router = useRouter();
  const { user } = useAuth();
  const isAdmin = (user as any)?.role === "admin";

  // State
  const [reports, setReports] = useState<Report[]>([]);
  const [loading, setLoading] = useState(true);
  const [filterStatus, setFilterStatus] = useState<"all" | "pending" | "resolved">("pending");
  const [processingReportId, setProcessingReportId] = useState<string | null>(null);
  const [toastState, setToastState] = useState<{
    show: boolean;
    type: ToastType;
    message: string;
  }>({ show: false, type: "success", message: "" });

  const triggerToast = (type: ToastType, message: string) => {
    setToastState({ show: true, type, message });
    setTimeout(() => {
      setToastState((prev) => ({ ...prev, show: false }));
    }, 3000);
  };

  // Redirect nếu không phải admin
  useEffect(() => {
    if (!user) {
      router.push("/login");
      return;
    }

    if (!isAdmin) {
      router.push("/");
      return;
    }
  }, [user, isAdmin, router]);

  // Fetch reports
  useEffect(() => {
    if (!isAdmin) return;

    const fetchReports = async () => {
      setLoading(true);
      try {
        const response = await getReports({
          status: filterStatus === "all" ? undefined : filterStatus,
        });

        if (response.status === "success") {
          setReports(response.data || []);
        } else {
          triggerToast("error", response.message || "Không thể tải báo cáo!");
        }
      } catch (error) {
        console.error("Fetch reports error:", error);
        triggerToast("error", "Lỗi khi tải báo cáo. Vui lòng thử lại!");
      } finally {
        setLoading(false);
      }
    };

    fetchReports();
  }, [isAdmin, filterStatus]);
// Xóa comment
  const handleDeleteComment = async (report: Report) => {
    if (!confirm("Bạn có chắc chắn muốn xóa bình luận này?")) return;

    setProcessingReportId(report.report_id);
    try {
      // 💡 ĐÃ SỬA: Truyền thêm user?.uid của Admin vào đây làm tham số thứ 3
      const response = await deleteCommentAsAdmin(
        report.restaurant_id,
        report.comment_id,
        user?.uid || "" 
      );

      if (response.status === "success") {
        // Cập nhật status báo cáo thành "resolved" trên database
        const updateResponse = await updateReportStatus(report.report_id, "resolved", "deleted");

        if (updateResponse.status === "success") {
          // 1. Cập nhật UI lập tức sang trạng thái "resolved" để hiện tag màu xanh
          setReports((prev) =>
            prev.map((r) =>
             r.report_id === report.report_id 
            ? { ...r, status: "resolved", type_resolve: "deleted" } 
            : r
            )
          );
          triggerToast("success", "Đã xóa bình luận và đóng báo cáo!");

          // 2. Tự động ẩn bản ghi này khỏi màn hình sau 3 giây cho gọn giao diện
          setTimeout(() => {
            setReports((prev) => prev.filter((r) => r.report_id !== report.report_id));
          }, 3000);
        }
      } else {
        triggerToast("error", response.message || "Không thể xóa bình luận!");
      }
    } catch (error) {
      console.error("Delete comment error:", error);
      triggerToast("error", "Lỗi khi xóa bình luận. Vui lòng thử lại!");
    } finally {
      setProcessingReportId(null);
    }
  };

  // Bỏ qua báo cáo (đánh dấu resolved mà không xóa)
  const handleDismissReport = async (reportId: string) => {
    setProcessingReportId(reportId);
    try {
      const response = await updateReportStatus(reportId, "resolved", "dismissed");

      if (response.status === "success") {
        setReports((prev) =>
          prev.map((r) =>
            r.report_id === reportId ? { ...r, status: "resolved",type_resolve: "dismissed" } : r
          )
        );
        triggerToast("success", "Đã bỏ qua báo cáo này!");
      } else {
        triggerToast("error", response.message || "Không thể bỏ qua báo cáo!");
      }
    } catch (error) {
      console.error("Dismiss report error:", error);
      triggerToast("error", "Lỗi khi bỏ qua báo cáo. Vui lòng thử lại!");
    } finally {
      setProcessingReportId(null);
    }
  };

  const handleDeleteReport = async (reportId: string) => {
  if (!confirm("Bạn có chắc chắn muốn xóa vĩnh viễn báo cáo này không?")) return;

  setProcessingReportId(reportId);
  try {
    // Giả sử bạn có hàm deleteReport trong api
    const response = await deleteReport(reportId); 

    if (response.status === "success") {
      setReports((prev) => prev.filter((r) => r.report_id !== reportId));
      triggerToast("success", "Đã xóa báo cáo!");
    } else {
      triggerToast("error", response.message || "Không thể xóa báo cáo!");
    }
  } catch (error) {
    triggerToast("error", "Lỗi khi xóa báo cáo!");
  } finally {
    setProcessingReportId(null);
  }
};
  // Điều hướng sang explore để xem context
  const handleViewContext = (report: Report) => {
    router.push(
      `/explore?action=review_report&resId=${report.restaurant_id}&commentId=${report.comment_id}`
    );
  };

  if (!isAdmin) {
    return (
      <div className="w-full h-screen flex items-center justify-center bg-slate-50">
        <div className="text-center">
          <AlertCircle className="w-12 h-12 text-slate-400 mx-auto mb-3" />
          <p className="text-slate-600 font-semibold">Bạn không có quyền truy cập trang này.</p>
        </div>
      </div>
    );
  }
  const getResolveLabel = (type: string | null) => {
  switch (type) {
    case "deleted": return "Đã xóa";
    case "dismissed": return "Đã bỏ qua";
    default: return "Đã giải quyết";
  }
};  
  const pendingCount = reports.filter((r) => r.status === "pending").length;
  const filteredReports = reports.filter(
    (r) => filterStatus === "all" || r.status === filterStatus
  );

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <div className="sticky top-0 z-40 border-b border-slate-200 bg-white">
        <div className="mx-auto max-w-6xl px-4 py-4 sm:px-6">
          <div className="flex items-center justify-between gap-4">
            <div>
              <h1 className="text-2xl font-bold text-slate-900">Admin Dashboard</h1>
              <p className="text-sm text-slate-600">Quản lý báo cáo bình luận vi phạm</p>
            </div>

            {/* Avatar */}
            <div className="flex items-center gap-3">
              <div className="text-right">
                <p className="text-sm font-semibold text-slate-900">
                  {user?.displayName || "Admin"}
                </p>
                <p className="text-xs text-slate-500">Admin</p>
              </div>
              <img
                src={
                  user?.photoURL ||
                  `https://ui-avatars.com/api/?name=${encodeURIComponent(
                    user?.displayName || "Admin"
                  )}&background=ff6b4a&color=fff`
                }
                alt="Admin Avatar"
                className="w-10 h-10 rounded-full object-cover border border-slate-200"
              />
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="mx-auto max-w-6xl px-4 py-8 sm:px-6">
        {/* Stats Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
          <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-semibold text-slate-600">Tổng báo cáo</p>
                <p className="text-3xl font-bold text-slate-900 mt-1">{reports.length}</p>
              </div>
              <div className="rounded-full bg-blue-50 p-3">
                <Flag className="w-6 h-6 text-blue-600" />
              </div>
            </div>
          </div>

          <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-semibold text-slate-600">Chưa xử lý</p>
                <p className="text-3xl font-bold text-amber-600 mt-1">{pendingCount}</p>
              </div>
              <div className="rounded-full bg-amber-50 p-3">
                <AlertCircle className="w-6 h-6 text-amber-600" />
              </div>
            </div>
          </div>

          <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-semibold text-slate-600">Đã xử lý</p>
                <p className="text-3xl font-bold text-emerald-600 mt-1">
                  {reports.length - pendingCount}
                </p>
              </div>
              
              <div className="rounded-full bg-emerald-50 p-3">
                <Check className="w-6 h-6 text-emerald-600" />
              </div>
            </div>
          </div>
        </div>

        {/* Filter & List */}
        <div className="rounded-2xl border border-slate-200 bg-white shadow-sm overflow-hidden">
          {/* Filter Tabs */}
          <div className="border-b border-slate-200 flex items-center">
            {(["all", "pending", "resolved"] as const).map((status) => (
              <button
                key={status}
                onClick={() => setFilterStatus(status)}
                className={`flex-1 px-4 py-4 text-sm font-semibold transition border-b-2 ${
                  filterStatus === status
                    ? "text-rose-600 border-rose-600"
                    : "text-slate-600 border-transparent hover:text-slate-900"
                }`}
              >
                {status === "all" && "Tất cả"}
                {status === "pending" && `Chưa xử lý (${pendingCount})`}
                {status === "resolved" && "Đã xử lý"}
              </button>
            ))}
          </div>

          {/* Reports List */}
          <div className="divide-y divide-slate-100">
            {loading ? (
              <div className="p-8 flex justify-center">
                <Loader2 className="w-6 h-6 text-slate-400 animate-spin" />
              </div>
            ) : filteredReports.length === 0 ? (
              <div className="p-8 text-center">
                <AlertCircle className="w-12 h-12 text-slate-300 mx-auto mb-3" />
                <p className="text-slate-600 font-semibold">
                  {filterStatus === "pending"
                    ? "Không có báo cáo chưa xử lý nào"
                    : "Không có báo cáo nào"}
                </p>
              </div>
            ) : (
              filteredReports.map((report) => (
                <div
                  key={report.report_id}
                  className={`p-6 hover:bg-slate-50 transition ${
                    report.status === "resolved" ? "opacity-60" : ""
                  }`}
                >
                  <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
                    {/* Content */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-2">
                        <Flag className="w-4 h-4 text-amber-600 shrink-0" />
                        <span className="text-sm font-bold text-slate-900">
                          {report.restaurant_name || `Nhà hàng #${report.restaurant_id}`}
                        </span>
                        {report.status === "pending" && (
                          <span className="inline-flex items-center rounded-full bg-amber-50 px-2 py-0.5 text-xs font-semibold text-amber-700">
                            Chờ xử lý
                          </span>
                        )}
                        {report.status === "resolved" && (
                          <div className="flex flex-col gap-1">
                            {/* Tag chính */}
                            <span className="inline-flex items-center rounded-full bg-emerald-50 px-2 py-0.5 text-xs font-semibold text-emerald-700">
                              Đã xử lý
                            </span>
                            {/* Tag type_resolve hiển thị thêm */}
                            {report.type_resolve && (
                              <span className="text-[10px] font-medium text-slate-500 uppercase tracking-wider">
                                ({getResolveLabel(report.type_resolve)})
                              </span>
                            )}
                          </div>
                        )}
                      </div>

                      <div className="mb-3 p-3 bg-slate-50 rounded-lg border border-slate-200">
                        <p className="text-xs text-slate-500 font-semibold mb-1">BÌNH LUẬN:</p>
                        <p className="text-sm text-slate-700 line-clamp-2">"{report.comment_text}"</p>
                      </div>

                      <div className="space-y-1.5">
                        <div>
                          <p className="text-xs text-slate-500 font-semibold">LÝ DO BÁO CÁO:</p>
                          <p className="text-sm text-slate-700">{report.reason}</p>
                        </div>
                        <div>
                          <p className="text-xs text-slate-500 font-semibold">NGÀY BÁO CÁO:</p>
                          <p className="text-sm text-slate-700">
                            {new Date(report.created_at).toLocaleString("vi-VN")}
                          </p>
                        </div>
                      </div>
                    </div>

                    {/* Actions */}
                    <div className="flex flex-wrap gap-2 sm:flex-col-reverse">
                      {report.type_resolve !== "deleted" && (
                        <button
                          onClick={() => handleViewContext(report)}
                          disabled={processingReportId === report.report_id}
                          className="inline-flex items-center justify-center gap-2 rounded-xl border border-blue-200 bg-blue-50 px-4 py-2 text-sm font-semibold text-blue-700 transition hover:bg-blue-100 disabled:opacity-50"
                        >
                          <Eye className="w-4 h-4" />
                          <span>Xem ngữ cảnh</span>
                        </button>
                      )}

                      {/* Nút Xóa báo cáo (Nút mới) */}
                      <button
                        onClick={() => handleDeleteReport(report.report_id)}
                        disabled={processingReportId === report.report_id}
                        className="inline-flex items-center justify-center gap-2 rounded-xl border border-slate-200 bg-white px-4 py-2 text-sm font-semibold text-slate-500 hover:bg-slate-100 hover:text-slate-900 transition disabled:opacity-50"
                      >
                        <Trash2 className="w-4 h-4" />
                        <span>Xóa báo cáo</span>
                      </button>
                      {report.status === "pending" && (
                        <>
                          <button
                            onClick={() => handleDeleteComment(report)}
                            disabled={processingReportId === report.report_id}
                            className="inline-flex items-center justify-center gap-2 rounded-xl bg-rose-50 border border-rose-200 px-4 py-2 text-sm font-semibold text-rose-600 transition hover:bg-rose-100 disabled:opacity-50"
                          >
                            {processingReportId === report.report_id ? (
                              <Loader2 className="w-4 h-4 animate-spin" />
                            ) : (
                              <Trash2 className="w-4 h-4" />
                            )}
                            Xóa
                          </button>

                          <button
                            onClick={() => handleDismissReport(report.report_id)}
                            disabled={processingReportId === report.report_id}
                            className="inline-flex items-center justify-center gap-2 rounded-xl border border-slate-200 bg-white px-4 py-2 text-sm font-semibold text-slate-700 transition hover:bg-slate-100 disabled:opacity-50"
                          >
                            <Check className="w-4 h-4" />
                            Bỏ qua
                          </button>
                        </>
                      )}
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="mt-8 text-center">
          <Link href="/" className="text-sm text-rose-600 hover:underline font-semibold">
            ← Quay lại trang chủ
          </Link>
        </div>
      </div>

      {/* Toast */}
      {toastState.show && (
        <Toast
          show={toastState.show}
          type={toastState.type}
          message={toastState.message}
          onClose={() => setToastState((prev) => ({ ...prev, show: false }))}
        />
      )}
    </div>
  );
}
