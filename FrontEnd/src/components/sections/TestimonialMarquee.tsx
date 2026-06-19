"use client";

import { Star } from "lucide-react";

const reviews = [
  {
    name: "Ngọc Anh",
    location: "Đà Nẵng",
    avatar: "NA",
    content:
      "BMI giúp mình tối ưu hành trình ăn uống mà không phải suy nghĩ nhiều. Lộ trình gợi ý hợp lý và dễ theo dõi."
  },
  {
    name: "Minh Quân",
    location: "TP Hồ Chí Minh",
    avatar: "MQ",
    content:
      "Trải nghiệm rất mượt, đặc biệt là phần vé lộ trình. Mình share lên mạng xã hội và ai cũng hỏi app này là gì."
  },
  {
    name: "Thanh Huy",
    location: "Hà Nội",
    avatar: "TH",
    content:
      "Gợi ý quán ăn chính xác, có cả tiêu chí không gian và mức giá. Mình thử ở nhiều khu vực đều ổn."
  },
  {
    name: "Hải Yến",
    location: "Đà Lạt",
    avatar: "HY",
    content:
      "Mình thích cách BMI tóm tắt lộ trình, nhìn một lần là hiểu cả ngày sẽ ăn gì, đi đâu."
  },
  {
    name: "Tuấn Anh",
    location: "Vũng Tàu",
    avatar: "TA",
    content:
      "Tính năng map và lọc khẩu vị cực kỳ hữu ích. Lịch trình phù hợp cho gia đình nên ai cũng thích."
  }
];

const marqueeReviews = [...reviews, ...reviews];

export default function TestimonialMarquee() {
  return (
    <section className="px-6 pb-20 pt-8">
      <div className="mx-auto w-full max-w-6xl space-y-8">
        <div className="space-y-3">
          <div className="text-sm font-semibold uppercase tracking-[0.3em] text-brand-lagoon">
            Người dùng nói gì
          </div>
          <h2 className="font-display text-3xl font-semibold text-slate-900 md:text-4xl">
            Đánh giá từ cộng đồng khám phá ẩm thực.
          </h2>
        </div>

        <div className="relative overflow-hidden">
          <div className="pointer-events-none absolute inset-y-0 left-0 w-24 bg-gradient-to-r from-white via-white/80 to-transparent" />
          <div className="pointer-events-none absolute inset-y-0 right-0 w-24 bg-gradient-to-l from-white via-white/80 to-transparent" />
          <div className="flex gap-6 hover:[animation-play-state:paused]">
            <div className="flex w-max gap-6 animate-marquee">
              {marqueeReviews.map((review, index) => (
                <div
                  key={`${review.name}-${index}`}
                  className="w-[min(82vw,350px)] rounded-2xl border border-slate-200/70 bg-white p-5 shadow-sm sm:w-[350px]"
                >
                  <div className="flex items-center gap-3">
                    <div className="flex h-12 w-12 items-center justify-center rounded-full bg-gradient-to-br from-brand-coral to-brand-flame text-white text-sm font-semibold">
                      {review.avatar}
                    </div>
                    <div>
                      <div className="text-sm font-semibold text-slate-900">
                        {review.name}
                      </div>
                      <div className="text-xs text-slate-500">
                        {review.location}
                      </div>
                    </div>
                  </div>
                  <div className="mt-3 flex items-center gap-1">
                    {Array.from({ length: 5 }).map((_, starIndex) => (
                      <Star
                        key={`${review.name}-star-${starIndex}`}
                        className="h-4 w-4 fill-yellow-400 text-yellow-400"
                      />
                    ))}
                  </div>
                  <p className="mt-3 line-clamp-4 text-sm text-slate-600">
                    {review.content}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
