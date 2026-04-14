import { ArrowRight, Brain, Calendar, ChevronRight, Globe, MessageSquare, Network, Tag, UploadCloud, Zap } from 'lucide-react';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

/** 后端配置的考试院地址常为 127.0.0.1；手机访问时 127.0.0.1 指向手机自身，需换成当前页所在主机名（如电脑局域网 IP）。 */
function rewriteLocalhostToolUrl(url: string): string {
  try {
    const parsed = new URL(url);
    if (parsed.hostname !== '127.0.0.1' && parsed.hostname !== 'localhost') {
      return url;
    }
    parsed.hostname = window.location.hostname;
    return parsed.href;
  } catch {
    return url;
  }
}

export default function EducationTools() {
  const navigate = useNavigate();
  const [isLaunchingCrawler, setIsLaunchingCrawler] = useState(false);

  const handleLaunchCrawler = async () => {
    if (isLaunchingCrawler) return;
    setIsLaunchingCrawler(true);
    try {
      const response = await fetch('/api/v1/tools/education-exam-crawler/status');
      if (!response.ok) {
        alert('暂时无法检查考试院信息收集工具状态，请稍后重试。');
        return;
      }
      const payload = await response.json();
      if (payload.configured && payload.reachable) {
        const raw = typeof payload.launch_url === 'string' ? payload.launch_url : '';
        const target = raw ? rewriteLocalhostToolUrl(raw) : '';
        if (target) {
          window.location.assign(target);
          return;
        }
        window.location.assign('/api/v1/tools/education-exam-crawler/launch');
        return;
      }
      alert(payload.message || '考试院信息收集工具暂不可用，请检查配置和服务状态。');
    } catch {
      alert('检查考试院信息收集工具状态失败，请确认后端服务已启动。');
    } finally {
      setIsLaunchingCrawler(false);
    }
  };

  return (
    <div className="min-h-screen bg-surface text-on-surface font-body relative overflow-x-hidden selection:bg-primary/20 flex flex-col">
      {/* Background Textures */}
      <div className="fixed inset-0 grid-bg z-0 pointer-events-none opacity-15"></div>
      <div className="fixed inset-0 grain-overlay z-10 pointer-events-none opacity-[0.03]"></div>

      {/* Top Navigation */}
      <header className="bg-surface-container-low/80 backdrop-blur-md flex justify-between items-center w-full px-6 md:px-12 py-6 max-w-[1920px] mx-auto sticky top-0 z-50 font-headline border-b border-outline-variant/10">
        <div className="flex items-center gap-4">
          <div className="flex flex-col">
            <nav className="flex items-center gap-2 text-[10px] text-on-secondary-container mb-1 uppercase tracking-widest font-label">
              <span className="hover:text-primary transition-colors cursor-pointer" onClick={() => navigate('/')}>Workbench</span>
              <ChevronRight size={12} />
              <span className="text-primary font-bold">教务工具</span>
            </nav>
            <h1 className="text-2xl font-bold text-primary tracking-tight">教务工具</h1>
          </div>
        </div>
        <div className="text-primary-container font-medium opacity-70 text-right leading-tight hidden lg:block text-sm whitespace-nowrap">
          连接咨询、教务与内容生产的全链路智能工具看板
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 px-6 md:px-12 pt-12 pb-32 max-w-5xl mx-auto w-full relative z-20">
        
        {/* Description Section */}
        <section className="mb-12 max-w-3xl">
          <p className="text-on-surface-variant text-lg leading-relaxed font-body">
            集成领先的 AI 能力，为教务流程提供全方位支持。从深度咨询话术分析到复杂的考试计划生成，助力每一位教育工作者实现精细化运营。
          </p>
        </section>

        {/* Tool Stack Section */}
        <section className="flex flex-col gap-8 mb-20">
          
          {/* Large Primary Card */}
          <div className="relative group bg-surface-container-lowest rounded-2xl p-8 md:p-10 transition-all duration-300">
            
            <div className="flex flex-col md:flex-row justify-between items-start gap-6 mb-8">
              <div className="flex-1">
                <h3 className="text-3xl font-headline font-extrabold text-primary mb-3">用户画像分析工具</h3>
                <p className="text-on-surface-variant text-lg max-w-2xl leading-relaxed">
                  深度解析学员沟通记录，通过语义识别提取核心痛点，自动构建动态用户画像，并实时生成针对性的跟进建议。
                </p>
              </div>
            </div>

            <button 
              onClick={() => navigate('/persona-analysis')}
              className="flex items-center gap-2 px-8 py-3.5 bg-primary text-on-primary rounded-xl font-bold text-sm hover:opacity-90 transition-opacity active:scale-95"
            >
              立即开始分析
              <ArrowRight size={16} />
            </button>
          </div>

          {/* Medium Card 1 */}
          <div className="bg-surface-container-lowest rounded-2xl p-8 md:p-10 flex flex-col md:flex-row gap-8 items-start group transition-all duration-300">
            <div className="flex-1">
              <h3 className="text-3xl font-headline font-extrabold text-primary mb-4">考试院信息收集工具</h3>
              <p className="text-on-surface-variant text-lg leading-relaxed max-w-3xl">
                全网实时抓取各地考试院动态，自动分类整理政策变动、报名时间及考位余额提醒。结合地理位置推送，确保不遗漏任何关键节点。
              </p>
              <button
                onClick={handleLaunchCrawler}
                disabled={isLaunchingCrawler}
                className="mt-8 flex items-center gap-2 px-8 py-3.5 bg-primary text-on-primary rounded-xl font-bold text-sm hover:opacity-90 transition-opacity active:scale-95"
              >
                {isLaunchingCrawler ? '检查服务状态中...' : '立即开始分析'}
                <ArrowRight size={16} />
              </button>
            </div>
            <div className="p-4 bg-surface-container-highest/30 rounded-2xl text-primary transition-colors">
              <Globe size={40} strokeWidth={1.5} />
            </div>
          </div>

          {/* Medium Card 2 */}
          <div className="bg-surface-container-low rounded-2xl p-8 md:p-10 flex flex-col md:flex-row gap-8 items-start group opacity-90 hover:opacity-100 transition-all">
            <div className="flex-1">
              <div className="flex items-center gap-3 mb-4">
                <span className="inline-flex items-center px-3 py-1 border border-outline-variant text-on-secondary-container rounded-full text-[10px] font-medium uppercase tracking-wider">
                  规划中
                </span>
                <span className="text-xs text-on-surface-variant italic">正在进行算法微调</span>
              </div>
              <h3 className="text-2xl font-headline font-bold text-on-surface mb-4">考试计划生成工具</h3>
              <p className="text-on-secondary-container leading-relaxed max-w-3xl">
                基于学员的基础能力数据，由 AI 自动排布最优复习路径与模拟考周期。支持动态调整计划，根据学员阶段性测试结果实时优化提分方案。
              </p>
            </div>
            <div className="p-4 bg-surface-container-highest/30 rounded-2xl text-on-secondary-container group-hover:text-primary transition-colors">
              <Calendar size={40} strokeWidth={1.5} />
            </div>
          </div>

        </section>
      </main>
    </div>
  );
}
