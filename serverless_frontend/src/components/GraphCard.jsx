import TestGraph1 from "./LDESgraphs/GraphLDES"; // Verify the path based on your file structure

const GraphCard = ({ title, GraphComponent }) => (
  <div className="bg-white overflow-hidden shadow rounded-lg border border-slate-200 flex flex-col">
    {/* Card Header */}
    <div className="px-4 py-5 sm:px-6 border-b border-slate-100">
      <h3 className="text-lg leading-6 font-medium text-slate-900">{title}</h3>
      <p className="mt-1 max-w-2xl text-sm text-slate-500">Real-time interaction enabled.</p>
    </div>
    
    {/* Graph Area */}
    <div className="p-6 flex-grow">
      {/* We keep 'aspect-video' to maintain the shape, but put the chart inside */}
      <div className="w-full aspect-video">
        <GraphComponent />
      </div>
    </div>
    
    {/* Card Footer */}
    <div className="bg-slate-50 px-4 py-4 sm:px-6">
      <button className="text-sm font-medium text-blue-600 hover:text-blue-500">
        View Full Details &rarr;
      </button>
    </div>
  </div>
);

export default GraphCard;