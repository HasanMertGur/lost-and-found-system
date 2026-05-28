import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ArrowLeft, MessageSquare, MapPin, Calendar, Info, Share2, AlertTriangle } from 'lucide-react';

export default function ItemDetail() {
   const { id } = useParams();
   const [item, setItem] = useState(null);
   const [loading, setLoading] = useState(true);

   useEffect(() => {
      // Backend'den ilanın kendi detaylarını çekiyoruz
      fetch(`http://127.0.0.1:5000/api/reports/${id}`)
         .then(res => res.json())
         .then(data => {
             if (data.message) {
                 console.error(data.message);
                 setItem(null);
             } else {
                 setItem(data);
             }
             setLoading(false);
         })
         .catch(err => {
             console.error("Veri çekilemedi:", err);
             setLoading(false);
         });
   }, [id]);

   if (loading) {
       return <div className="text-center py-20 text-gray-600 font-medium text-lg">İlan yükleniyor...</div>;
   }

   if (!item) {
       return <div className="text-center py-20 text-red-500 font-medium text-lg">İlan bulunamadı!</div>;
   }

   return (
      <div className="max-w-4xl mx-auto space-y-6">
         <Link to="/" className="inline-flex items-center text-sm font-medium text-gray-500 hover:text-indigo-600 transition-colors">
            <ArrowLeft className="mr-2 h-4 w-4" /> İlanlara Dön
         </Link>

         <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
            {/* Görsel Alanı */}
            <div className="relative h-64 sm:h-80 md:h-96 w-full bg-gray-200 flex items-center justify-center">
               <span className="text-gray-400 font-medium text-xl">Görsel Yok</span>
               <div className="absolute top-4 left-4 flex gap-2">
                  <span className={`px-4 py-1.5 rounded-full text-sm font-bold uppercase tracking-wider text-white shadow-md ${item.type === 'lost' ? 'bg-red-500' : 'bg-green-500'}`}>
                     {item.type}
                  </span>
                  <span className="px-4 py-1.5 rounded-full text-sm font-bold uppercase tracking-wider text-indigo-700 bg-indigo-100 shadow-md">
                     {item.category_name}
                  </span>
               </div>
            </div>

            <div className="p-6 md:p-8">
               <div className="flex flex-col md:flex-row md:justify-between md:items-start gap-4 mb-6">
                  <div>
                     <h1 className="text-3xl font-extrabold text-gray-900 mb-2">{item.item_name}</h1>
                     <p className="text-gray-500 flex items-center">
                        Ekleyen: <span className="font-semibold text-gray-700 ml-1">{item.reported_by}</span>
                        <span className="mx-2">•</span>
                        <span>Tarih: {new Date(item.created_at).toLocaleDateString()}</span>
                     </p>
                  </div>

                  <div className="flex items-center gap-3">
                     <button className="flex-1 md:flex-none flex items-center justify-center p-3 text-gray-600 bg-gray-50 hover:bg-gray-100 rounded-lg border border-gray-200 transition-colors">
                        <Share2 className="h-5 w-5" />
                     </button>
                     <button className="flex-1 md:flex-none flex items-center justify-center px-6 py-3 bg-indigo-600 hover:bg-indigo-700 text-white font-medium rounded-lg shadow-sm transition-colors">
                        <MessageSquare className="mr-2 h-5 w-5" /> {item.type === 'lost' ? 'Sahibine' : 'Bulana'} Mesaj At
                     </button>
                  </div>
               </div>

               <div className="grid grid-cols-1 md:grid-cols-3 gap-8 py-6 border-y border-gray-100">
                  <div className="col-span-2 space-y-6">
                     <div>
                        <h3 className="text-lg font-bold text-gray-900 mb-3 flex items-center">
                           <Info className="mr-2 h-5 w-5 text-indigo-500" /> Açıklama
                        </h3>
                        <p className="text-gray-600 leading-relaxed whitespace-pre-wrap">{item.description}</p>
                     </div>
                  </div>

                  <div className="space-y-4 bg-gray-50 p-6 rounded-xl border border-gray-100">
                     <h3 className="font-bold text-gray-900 border-b border-gray-200 pb-2">Detaylar</h3>

                     <div className="space-y-4">
                        <div>
                           <span className="text-sm font-medium text-gray-500 block mb-1">Durum</span>
                           <div className="flex items-center">
                              <span className="flex h-3 w-3 relative mr-2">
                                 <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                                 <span className="relative inline-flex rounded-full h-3 w-3 bg-green-500"></span>
                              </span>
                              <span className="font-medium text-gray-900 capitalize">{item.status}</span>
                           </div>
                        </div>

                        <div>
                           <span className="text-sm font-medium text-gray-500 block mb-1">Konum</span>
                           <div className="flex items-start text-gray-900 font-medium">
                              <MapPin className="mr-2 h-5 w-5 text-gray-400 shrink-0 mt-0.5" />
                              <span>{item.location}</span>
                           </div>
                        </div>

                        <div>
                           <span className="text-sm font-medium text-gray-500 block mb-1">Kayıt Tarihi</span>
                           <div className="flex items-center text-gray-900 font-medium">
                              <Calendar className="mr-2 h-5 w-5 text-gray-400 shrink-0" />
                              <span>{new Date(item.created_at).toLocaleDateString()}</span>
                           </div>
                        </div>
                     </div>
                     
                     <div className="mt-6 pt-4 border-t border-gray-200">
                        <button className="flex items-center text-sm font-medium text-red-600 hover:text-red-800 transition-colors">
                           <AlertTriangle className="mr-2 h-4 w-4" /> İlanı Şikayet Et
                        </button>
                     </div>
                  </div>
               </div>

            </div>
         </div>
      </div>
   );
}