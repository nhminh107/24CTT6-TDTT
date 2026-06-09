"use client";

import React, { useEffect, useState } from "react";
import axios from "axios";
import { X, Star, MapPin, Phone, Info, AlertTriangle, ThumbsUp, ThumbsDown, Edit3, Trash2 } from "lucide-react";
import { Restaurant } from "@/lib/utils";
import { useAuth } from "@/context/AuthContext";
interface RestaurantDetailModalProps {
  restaurant: Restaurant | null;
  isOpen: boolean;
  onClose: () => void;
}

interface CommentItem {
  comment_id: string;
  user_id: string;
  username: string;
  content: string;
  like_count: number;
  dislike_count: number;
  created_at?: string;
  updated_at?: string | null;
  edited?: boolean;
  current_vote?: "like" | "dislike" | null; // trạng thái vote của user hiện tại
}

// TODO: Thay bằng user thật từ auth context của bạn


export default function RestaurantDetailModal({
  restaurant,
  isOpen,
  onClose,
}: RestaurantDetailModalProps) {
  const [comments, setComments] = useState<CommentItem[]>([]);
  const [newComment, setNewComment] = useState("");
  const [loadingComments, setLoadingComments] = useState(false);
  const [submittingComment, setSubmittingComment] = useState(false);
  const [votingCommentId, setVotingCommentId] = useState<string | null>(null);
  const [editingCommentId, setEditingCommentId] = useState<string | null>(null);
  const [editingCommentContent, setEditingCommentContent] = useState("");
  const [processingCommentId, setProcessingCommentId] = useState<string | null>(null);
  const { user } = useAuth();

  const CURRENT_USER = {
    user_id: user?.uid || "anonymous_user_id",
    username: user?.displayName || "Anonymous",
  };

  useEffect(() => {
    if (!isOpen || !restaurant?.id) return;
    setComments([]);
    fetchComments();  
  }, [isOpen, restaurant?.id]);

  const fetchComments = async () => {
    setLoadingComments(true);
    try {
      const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/user/restaurant-comment/${restaurant!.id}?user_id=${CURRENT_USER.user_id}`
      );
      if (!res.ok) return;
      const data = await res.json();
      // Backend trả về: { restaurant_id, total_comments, comments: [...] }
      setComments(
        (data.comments ?? []).map((c: CommentItem) => ({
          ...c,
          edited: c.edited ?? false,
          updated_at: c.updated_at ?? null,
        }))
      );
    } catch (error) {
      console.error("Fetch comments failed", error);
    } finally {
      setLoadingComments(false);
    }
  };

  const handleSubmitComment = async () => {
    if (!restaurant?.id || !newComment.trim()) return;
    setSubmittingComment(true);
    try {
      await axios.post(
        `${process.env.NEXT_PUBLIC_API_URL}/api/user/restaurant-comment/${restaurant.id}`,
        {
          user_id: CURRENT_USER.user_id,
          username: CURRENT_USER.username,
          content: newComment.trim(),
        },
        { headers: { "Content-Type": "application/json" } }
      );
      await fetchComments();
      setNewComment("");
    } catch (error: any) {
      console.error("Submit comment failed", error);
    } finally {
      setSubmittingComment(false);
    }
  };

  const handleVote = async (commentId: string, voteType: "like" | "dislike") => {
    if (!restaurant?.id || !commentId || votingCommentId) return;
    setVotingCommentId(commentId);

    try {
      const { data } = await axios.post(
        `${process.env.NEXT_PUBLIC_API_URL}/api/user/restaurant-comment/${restaurant.id}/${commentId}/vote`,
        {
          user_id: CURRENT_USER.user_id,
          vote_type: voteType,
        },
        { headers: { "Content-Type": "application/json" } }
      );

      const newCurrentVote = data.current_vote as "like" | "dislike" | null;

      setComments((prev) =>
        prev.map((comment) => {
          if (comment.comment_id !== commentId) return comment;

          const prevVote = comment.current_vote;
          let { like_count, dislike_count } = comment;

          if (prevVote === "like") like_count -= 1;
          if (prevVote === "dislike") dislike_count -= 1;
          if (newCurrentVote === "like") like_count += 1;
          if (newCurrentVote === "dislike") dislike_count += 1;

          return { ...comment, like_count, dislike_count, current_vote: newCurrentVote };
        })
      );
    } catch (error: any) {
      console.error("Vote failed", error);
    } finally {
      setVotingCommentId(null);
    }
  };

  const startEditComment = (comment: CommentItem) => {
    setEditingCommentId(comment.comment_id);
    setEditingCommentContent(comment.content);
  };

  const cancelEdit = () => {
    setEditingCommentId(null);
    setEditingCommentContent("");
  };

  const handleSaveEdit = async (commentId: string) => {
    if (!restaurant?.id || !editingCommentContent.trim()) return;
    setProcessingCommentId(commentId);

    try {
      await axios.put(
        `${process.env.NEXT_PUBLIC_API_URL}/api/user/restaurant-comment/${restaurant.id}/${commentId}`,
        {
          user_id: CURRENT_USER.user_id,
          content: editingCommentContent.trim(),
        },
        { headers: { "Content-Type": "application/json" } }
      );

      setComments((prev) =>
        prev.map((comment) =>
          comment.comment_id === commentId
            ? {
                ...comment,
                content: editingCommentContent.trim(),
                edited: true,
                updated_at: new Date().toISOString(),
              }
            : comment
        )
      );
      cancelEdit();
    } catch (error: any) {
      console.error("Edit comment failed", error);
    } finally {
      setProcessingCommentId(null);
    }
  };

  const handleDeleteComment = async (commentId: string) => {
    if (!restaurant?.id) return;
    setProcessingCommentId(commentId);

    try {
      await axios.delete(
        `${process.env.NEXT_PUBLIC_API_URL}/api/user/restaurant-comment/${restaurant.id}/${commentId}`,
        {
          headers: { "Content-Type": "application/json" },
          data: { user_id: CURRENT_USER.user_id },
        }
      );

      setComments((prev) => prev.filter((comment) => comment.comment_id !== commentId));
      if (editingCommentId === commentId) cancelEdit();
    } catch (error: any) {
      console.error("Delete comment failed", error);
    } finally {
      setProcessingCommentId(null);
    }
  };

  if (!isOpen || !restaurant) return null;

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
      <div className="relative w-full max-w-2xl max-h-[90vh] overflow-y-auto bg-white rounded-2xl shadow-2xl">
        <button
          onClick={onClose}
          className="absolute top-4 right-4 z-10 p-2 bg-white/80 backdrop-blur-md rounded-full text-slate-600 hover:text-rose-500 transition-colors shadow-sm"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Hero Image */}
        <div className="relative h-64 sm:h-80 w-full overflow-hidden">
          <img
            src={restaurant.imageUrl || "/assets/images/AI.png"}
            alt={restaurant.name}
            className="w-full h-full object-cover"
          />
          <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent" />
          <div className="absolute bottom-6 left-6 right-6 text-white">
            <h2 className="text-3xl font-bold mb-2">{restaurant.name}</h2>
            <div className="flex items-center gap-2">
              <div className="flex items-center bg-yellow-400 px-2 py-0.5 rounded-full text-xs font-bold text-black">
                <Star className="w-3 h-3 fill-current mr-1" />
                {restaurant.rating}
              </div>
              <span className="text-sm font-medium opacity-90">
                • {restaurant.price.toLocaleString()} VNĐ
              </span>
            </div>
          </div>
        </div>

        <div className="p-6 sm:p-8 space-y-8">
          {/* Info Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
            <div className="space-y-4">
              <div className="flex items-start gap-3">
                <div className="mt-1 p-2 bg-rose-50 rounded-lg">
                  <MapPin className="w-5 h-5 text-rose-500" />
                </div>
                <div>
                  <h4 className="text-sm font-semibold text-slate-500 uppercase tracking-wider">Địa chỉ</h4>
                  <p className="text-slate-800 font-medium">{restaurant.address}</p>
                  <a
                    href={restaurant.mapUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-sm text-rose-500 hover:underline inline-block mt-1 font-medium"
                  >
                    Xem trên Google Maps
                  </a>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <div className="mt-1 p-2 bg-blue-50 rounded-lg">
                  <Phone className="w-5 h-5 text-blue-500" />
                </div>
                <div>
                  <h4 className="text-sm font-semibold text-slate-500 uppercase tracking-wider">Điện thoại</h4>
                  <p className="text-slate-800 font-medium">{restaurant.phone || "Không có số điện thoại"}</p>
                </div>
              </div>
            </div>

            <div className="p-4 bg-slate-50 rounded-xl space-y-3 border border-slate-100">
              <h4 className="flex items-center gap-2 text-sm font-bold text-slate-700 uppercase tracking-wider">
                <Info className="w-4 h-4" />
                Giới thiệu
              </h4>
              <p className="text-slate-600 text-sm leading-relaxed">{restaurant.semanticText}</p>
            </div>
          </div>

          {/* Health Analysis */}
          {((restaurant.warnings?.length ?? 0) > 0 || (restaurant.notes?.length ?? 0) > 0) && (
            <div className="space-y-4 pt-6 border-t border-slate-100">
              <h3 className="text-xl font-bold text-slate-800">Phân tích sức khỏe</h3>
              {restaurant.warnings && restaurant.warnings.length > 0 && (
                <div className="space-y-3">
                  {restaurant.warnings.map((warning, idx) => (
                    <div key={idx} className="flex gap-3 p-4 bg-amber-50 rounded-xl border border-amber-100">
                      <AlertTriangle className="w-5 h-5 text-amber-500 shrink-0" />
                      <p className="text-amber-800 text-sm font-medium leading-relaxed">{warning}</p>
                    </div>
                  ))}
                </div>
              )}
              {restaurant.notes && restaurant.notes.length > 0 && (
                <div className="space-y-3">
                  {restaurant.notes.map((note, idx) => (
                    <div key={idx} className="p-4 bg-slate-50 rounded-xl border border-slate-200">
                      <p className="text-slate-700 text-sm leading-relaxed italic">{note}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Meals */}
          {Array.isArray(restaurant.meals) && restaurant.meals.length > 0 && (
            <div className="space-y-4 pt-6 border-t border-slate-100">
              <h4 className="text-sm font-bold text-slate-500 uppercase tracking-wider">Phục vụ các bữa</h4>
              <div className="flex flex-wrap gap-2">
                {restaurant.meals.map((meal, idx) => (
                  <span key={idx} className="px-4 py-1.5 bg-slate-100 text-slate-600 rounded-full text-sm font-bold capitalize">
                    {meal}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Comments */}
          <div className="pt-6 border-t border-slate-100">
            <div>
              <h3 className="text-xl font-bold text-slate-800">Bình luận</h3>
              <p className="text-sm text-slate-500">Chia sẻ trải nghiệm của bạn về nhà hàng này.</p>
            </div>

            <div className="mt-4 space-y-4">
              {/* Input */}
              <div className="flex flex-col gap-3">
                <textarea
                  value={newComment}
                  onChange={(e) => setNewComment(e.target.value)}
                  rows={4}
                  placeholder="Viết bình luận của bạn..."
                  className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-900 placeholder:text-slate-400 outline-none focus:border-rose-400 focus:ring-4 focus:ring-rose-100 transition"
                />
                <button
                  onClick={handleSubmitComment}
                  disabled={submittingComment || !newComment.trim()}
                  className="inline-flex items-center justify-center rounded-2xl bg-rose-500 px-5 py-3 text-sm font-bold text-white transition hover:bg-rose-600 disabled:cursor-not-allowed disabled:bg-slate-300"
                >
                  {submittingComment ? "Đang gửi..." : "Gửi bình luận"}
                </button>
              </div>

              {/* List */}
              <div className="space-y-4">
                {loadingComments ? (
                  <div className="rounded-2xl border border-slate-200 bg-slate-50 p-6 text-center text-sm text-slate-500">
                    Đang tải bình luận...
                  </div>
                ) : comments.length === 0 ? (
                  <div className="rounded-2xl border border-slate-200 bg-slate-50 p-6 text-center text-sm text-slate-500">
                    Chưa có bình luận nào. Hãy là người đầu tiên nhận xét!
                  </div>
                ) : (
                  comments.map((comment) => {
                    const isOwnComment = comment.user_id === CURRENT_USER.user_id;
                    const isEditing = editingCommentId === comment.comment_id;

                    return (
                      <div
                        key={comment.comment_id}
                        className={`rounded-3xl border p-5 shadow-sm ${
                          isOwnComment
                            ? "border-rose-300 bg-rose-50/40"
                            : "border-slate-200 bg-white"
                        }`}
                      >
                        <div className="flex flex-col gap-3">
                          <div className="flex items-start justify-between gap-4">
                            <div>
                              <div className="flex items-center gap-2">
                                <p className="text-sm font-semibold text-slate-900">{comment.username}</p>
                                {isOwnComment && (
                                  <span className="rounded-full bg-rose-100 px-2 py-0.5 text-[11px] font-semibold uppercase tracking-[0.2em] text-rose-600">
                                    Bạn
                                  </span>
                                )}
                              </div>
                              <p className="text-xs text-slate-400">
                                {comment.created_at ?? "Vừa xong"}
                                {comment.edited && " • (đã chỉnh sửa)"}
                              </p>
                            </div>
                            <div className="flex items-center gap-2 text-xs text-slate-500">
                              <span>{comment.like_count} thích</span>
                              <span>•</span>
                              <span>{comment.dislike_count} không thích</span>
                            </div>
                          </div>

                          {isEditing ? (
                            <div className="space-y-3">
                              <textarea
                                value={editingCommentContent}
                                onChange={(e) => setEditingCommentContent(e.target.value)}
                                rows={4}
                                className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900 outline-none focus:border-rose-400 focus:ring-4 focus:ring-rose-100"
                              />
                              <div className="flex flex-wrap gap-2">
                                <button
                                  onClick={() => handleSaveEdit(comment.comment_id)}
                                  disabled={processingCommentId === comment.comment_id || !editingCommentContent.trim()}
                                  className="inline-flex items-center justify-center rounded-2xl bg-rose-500 px-4 py-2 text-sm font-bold text-white transition hover:bg-rose-600 disabled:cursor-not-allowed disabled:bg-slate-300"
                                >
                                  Lưu
                                </button>
                                <button
                                  onClick={cancelEdit}
                                  className="inline-flex items-center justify-center rounded-2xl border border-slate-200 bg-white px-4 py-2 text-sm font-semibold text-slate-700 transition hover:bg-slate-100"
                                >
                                  Hủy
                                </button>
                              </div>
                            </div>
                          ) : (
                            <>
                              <p className="text-sm leading-relaxed text-slate-700">{comment.content}</p>
                              <div className="mt-4 flex flex-wrap items-center gap-2">
                                <button
                                  onClick={() => handleVote(comment.comment_id, "like")}
                                  disabled={!!votingCommentId}
                                  className={`inline-flex items-center gap-2 rounded-full border px-4 py-2 text-sm font-semibold transition disabled:opacity-50 ${
                                    comment.current_vote === "like"
                                      ? "border-rose-400 bg-rose-50 text-rose-600"
                                      : "border-slate-200 bg-slate-50 text-slate-700 hover:border-rose-300 hover:text-rose-600"
                                  }`}
                                >
                                  <ThumbsUp className="w-4 h-4" />
                                  Thích
                                </button>
                                <button
                                  onClick={() => handleVote(comment.comment_id, "dislike")}
                                  disabled={!!votingCommentId}
                                  className={`inline-flex items-center gap-2 rounded-full border px-4 py-2 text-sm font-semibold transition disabled:opacity-50 ${
                                    comment.current_vote === "dislike"
                                      ? "border-blue-400 bg-blue-50 text-blue-600"
                                      : "border-slate-200 bg-slate-50 text-slate-700 hover:border-blue-300 hover:text-blue-600"
                                  }`}
                                >
                                  <ThumbsDown className="w-4 h-4" />
                                  Không thích
                                </button>
                                {isOwnComment && (
                                  <div className="ml-auto flex items-center gap-2">
                                    <button
                                      onClick={() => startEditComment(comment)}
                                      className="inline-flex items-center gap-2 rounded-full border border-slate-200 bg-white px-4 py-2 text-sm font-semibold text-slate-700 transition hover:bg-slate-100"
                                    >
                                      <Edit3 className="w-4 h-4" />
                                      Sửa
                                    </button>
                                    <button
                                      onClick={() => handleDeleteComment(comment.comment_id)}
                                      disabled={processingCommentId === comment.comment_id}
                                      className="inline-flex items-center gap-2 rounded-full border border-slate-200 bg-white px-4 py-2 text-sm font-semibold text-slate-700 transition hover:bg-slate-100 disabled:opacity-50"
                                    >
                                      <Trash2 className="w-4 h-4" />
                                      Xóa
                                    </button>
                                  </div>
                                )}
                              </div>
                            </>
                          )}
                        </div>
                      </div>
                    );
                  })
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}