import { ArrowRight, FileText, GraduationCap } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export default function Landing() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-surface text-on-surface font-body relative overflow-x-hidden selection:bg-primary/20">
      {/* Background Textures */}
      <div className="fixed inset-0 grid-bg z-0 pointer-events-none opacity-15"></div>
      <div className="fixed inset-0 grain-overlay z-10 pointer-events-none opacity-[0.03]"></div>

      {/* Top Navigation */}
      <nav className="bg-surface-container-low/80 backdrop-blur-md flex justify-between items-center w-full px-6 md:px-12 py-6 max-w-[1920px] mx-auto sticky top-0 z-50 font-headline border-b border-outline-variant/10">
        <div className="text-2xl font-bold text-primary tracking-tight">
          朗玛峰 AI 工作台
        </div>
        <div className="text-primary-container font-medium opacity-70 text-right leading-tight hidden lg:block text-sm whitespace-nowrap">
          连接咨询、教务与内容生产的智能工具看板
        </div>
      </nav>

      {/* Main Content */}
      <main className="relative z-20 max-w-7xl mx-auto px-6 pt-16 md:pt-24 pb-48">
        
        {/* Hero Section */}
        <header className="text-center mb-24">
          <h1 className="font-headline text-5xl md:text-7xl font-extrabold tracking-tighter text-primary mb-8">
            朗玛峰 AI 工作台
          </h1>
          
          {/* Scrolling Slogan Area */}
          <div className="h-10 overflow-hidden relative max-w-3xl mx-auto mask-image-linear-gradient">
            <div className="flex flex-col items-center gap-4 animate-scroll-y">
              <span className="text-xl md:text-2xl text-on-secondary-container font-medium h-10 flex items-center">高风险预警</span>
              <span className="text-xl md:text-2xl text-on-secondary-container font-medium h-10 flex items-center">客户画像分析</span>
              <span className="text-xl md:text-2xl text-on-secondary-container font-medium h-10 flex items-center">考试通知收集</span>
              <span className="text-xl md:text-2xl text-on-secondary-container font-medium h-10 flex items-center">考试计划生成</span>
              <span className="text-xl md:text-2xl text-on-secondary-container font-medium h-10 flex items-center">内容分发协同</span>
              {/* Duplicate first item for seamless loop */}
              <span className="text-xl md:text-2xl text-on-secondary-container font-medium h-10 flex items-center">高风险预警</span>
            </div>
          </div>
        </header>

        {/* Tools Grid */}
        <section className="grid grid-cols-1 md:grid-cols-2 gap-8 md:gap-12 max-w-6xl mx-auto">
          
          {/* Education Admin Tools Card */}
          <div 
            onClick={() => navigate('/education-tools')}
            className="group relative bg-surface-container-lowest rounded-2xl p-8 md:p-10 transition-all duration-300 hover:shadow-[0_8px_32px_rgba(0,0,0,0.04)] hover:bg-surface-bright cursor-pointer border border-outline-variant/15 flex flex-col h-full"
          >
            <div className="flex justify-between items-start mb-12">
              <div className="p-4 bg-primary/5 rounded-2xl text-primary group-hover:scale-110 transition-transform duration-300">
                <GraduationCap size={32} strokeWidth={1.5} />
              </div>
              <ArrowRight className="text-outline transition-transform duration-300 group-hover:translate-x-2 group-hover:text-primary" size={24} />
            </div>
            
            <div className="flex-grow">
              <h3 className="font-headline text-3xl font-bold text-primary mb-4 tracking-tight">教务工具</h3>
              <p className="text-on-secondary-container mb-10 leading-relaxed max-w-sm text-base">
                通过智能化的教务管理，自动收集考试信息并生成针对性的学习与考试计划。
              </p>
            </div>

            <div className="flex flex-wrap gap-2 mt-auto">
              <span className="px-4 py-1.5 bg-surface-container-low text-on-surface-variant text-xs font-semibold rounded-full border border-outline-variant/10">用户画像</span>
              <span className="px-4 py-1.5 bg-surface-container-low text-on-surface-variant text-xs font-semibold rounded-full border border-outline-variant/10">考试通知</span>
              <span className="px-4 py-1.5 bg-surface-container-low text-on-surface-variant text-xs font-semibold rounded-full border border-outline-variant/10">考试计划</span>
            </div>
          </div>

          {/* Content Tools Card (Disabled/Planned State) */}
          <div className="group relative bg-surface-container-lowest rounded-2xl p-8 md:p-10 opacity-75 grayscale-[0.3] transition-all duration-300 cursor-not-allowed border border-outline-variant/15 flex flex-col h-full">
            <div className="flex justify-between items-start mb-12">
              <div className="p-4 bg-secondary-container/30 rounded-2xl text-secondary">
                <FileText size={32} strokeWidth={1.5} />
              </div>
              <span className="px-3 py-1 bg-on-surface text-surface text-[10px] font-bold tracking-widest uppercase rounded-md">
                规划中
              </span>
            </div>
            
            <div className="flex-grow">
              <h3 className="font-headline text-3xl font-bold text-primary mb-4 tracking-tight">内容工具</h3>
              <p className="text-on-secondary-container mb-10 leading-relaxed max-w-sm text-base">
                一站式内容分发与协同工具，赋能跨平台任务回执与高效团队生产。
              </p>
            </div>

            <div className="flex flex-wrap gap-2 mt-auto">
              <span className="px-4 py-1.5 bg-surface-container-low text-on-surface-variant text-xs font-semibold rounded-full border border-outline-variant/10">多平台分发</span>
              <span className="px-4 py-1.5 bg-surface-container-low text-on-surface-variant text-xs font-semibold rounded-full border border-outline-variant/10">任务回执</span>
              <span className="px-4 py-1.5 bg-surface-container-low text-on-surface-variant text-xs font-semibold rounded-full border border-outline-variant/10">发布协同</span>
            </div>
          </div>

        </section>
      </main>

      {/* Footer */}
      <footer className="bg-surface-container-high/90 fixed bottom-0 w-full z-40 border-t border-outline-variant/15 backdrop-blur-md font-body text-xs tracking-wide">
        <div className="flex justify-between items-center px-6 md:px-12 py-4 max-w-[1920px] mx-auto">
          <div className="text-on-secondary-container opacity-80">
            结果仅供老师参考，需人工判断
          </div>
        </div>
      </footer>
      
      {/* Add inline style for the mask image used in the scrolling text */}
      <style dangerouslySetInnerHTML={{__html: `
        .mask-image-linear-gradient {
          mask-image: linear-gradient(to bottom, transparent, black 20%, black 80%, transparent);
          -webkit-mask-image: linear-gradient(to bottom, transparent, black 20%, black 80%, transparent);
        }
      `}} />
    </div>
  );
}
