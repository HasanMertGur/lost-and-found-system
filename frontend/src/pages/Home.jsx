import { useState } from 'react';
import { Link } from 'react-router-dom';
import { MapPin, Calendar, Search } from 'lucide-react';

const mockItems = [
   { id: 1, name: 'iPhone 13 Pro', type: 'lost', category: 'Elektronik', location: 'Kadikoy, Istanbul', date: '2026-05-20', description: 'Siyah renkli, kılıfı var.', image: 'https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?w=300&h=200&fit=crop' },
   { id: 2, name: 'Deri Cüzdan', type: 'found', category: 'Cüzdan & Çanta', location: 'Besiktas Sahil', date: '2026-05-22', description: 'İçinde kimlik ve kartlar bulunuyor.', image: 'https://images.unsplash.com/photo-1627123424574-724758594e93?w=300&h=200&fit=crop' },
   { id: 3, name: 'Toyota Araba Anahtarı', type: 'lost', category: 'Anahtarlık', location: 'Metro İçi, Levent', date: '2026-05-23', description: 'Ucunda küçük bir ayıcık anahtarlık var.', image: 'https://images.unsplash.com/photo-1582139329536-e7284fece509?w=300&h=200&fit=crop' },
   { id: 4, name: 'MacBook Pro İçeren Çanta', type: 'found', category: 'Cüzdan & Çanta', location: 'Kadıköy Kafe', date: '2026-05-24', description: 'Siyah sırt çantası.', image: 'https://images.unsplash.com/photo-1491897554428-130a60dd4757?w=300&h=200&fit=crop' },
];

export default function Home() {
   const [filter, setFilter] = useState('all');
   const [search, setSearch] = useState('');

   const filteredItems = mockItems.filter(item => {
      if (filter !== 'all' && item.type !== filter) return false;
      if (search && !item.name.toLowerCase().includes(search.toLowerCase()) && !item.location.toLowerCase().includes(search.toLowerCase())) return false;
      return true;
   });

   return (
      <div className="space-y-6">
         {/* Search Header */}
         <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 flex flex-col md:flex-row gap-4 justify-between items-center">
            <div className="relative w-full md:w-96">
               <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Search className="h-5 w-5 text-gray-400" />
               </div>
               <input
                  type="text"
                  className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-lg leading-5 bg-white placeholder-gray-500 focus:outline-none focus:placeholder-gray-400 focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                  placeholder="Search items by name or location..."
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
               />
            </div>

            <div className="flex bg-gray-100 p-1 rounded-lg">
               <button
                  className={`px-4 py-2 text-sm font-medium rounded-md transition-colors ${filter === 'all' ? 'bg-white shadow text-gray-900' : 'text-gray-500 hover:text-gray-900'}`}
                  onClick={() => setFilter('all')}
               >
                  All Items
               </button>
               <button
                  className={`px-4 py-2 text-sm font-medium rounded-md transition-colors ${filter === 'lost' ? 'bg-white shadow text-red-600' : 'text-gray-500 hover:text-red-600'}`}
                  onClick={() => setFilter('lost')}
               >
                  Lost
               </button>
               <button
                  className={`px-4 py-2 text-sm font-medium rounded-md transition-colors ${filter === 'found' ? 'bg-white shadow text-green-600' : 'text-gray-500 hover:text-green-600'}`}
                  onClick={() => setFilter('found')}
               >
                  Found
               </button>
            </div>
         </div>

         {/* Grid */}
         <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 xl:gap-8">
            {filteredItems.map(item => (
               <div key={item.id} className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden hover:shadow-md transition-shadow group flex flex-col">
                  <div className="relative h-48 overflow-hidden bg-gray-200">
                     <img src={item.image} alt={item.name} className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300" />
                     <div className={`absolute top-3 right-3 px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider text-white ${item.type === 'lost' ? 'bg-red-500' : 'bg-green-500'}`}>
                        {item.type}
                     </div>
                  </div>

                  <div className="p-5 flex-grow flex flex-col">
                     <div className="text-xs font-semibold text-indigo-600 mb-1">{item.category}</div>
                     <h3 className="text-lg font-bold text-gray-900 mb-2">{item.name}</h3>
                     <p className="text-sm text-gray-600 line-clamp-2 mb-4 flex-grow">{item.description}</p>

                     <div className="space-y-2 text-sm text-gray-500 mb-4">
                        <div className="flex items-center">
                           <MapPin className="h-4 w-4 mr-2" />
                           {item.location}
                        </div>
                        <div className="flex items-center">
                           <Calendar className="h-4 w-4 mr-2" />
                           {new Date(item.date).toLocaleDateString()}
                        </div>
                     </div>

                     <Link to={`/item/${item.id}`} className="mt-auto block w-full text-center bg-gray-50 border border-gray-200 text-gray-900 py-2 rounded-lg font-medium hover:bg-indigo-50 hover:text-indigo-700 hover:border-indigo-200 transition-colors">
                        View Details
                     </Link>
                  </div>
               </div>
            ))}
         </div>

         {filteredItems.length === 0 && (
            <div className="text-center py-12">
               <p className="text-gray-500 text-lg">No items found matching your criteria.</p>
            </div>
         )}
      </div>
   );
}
