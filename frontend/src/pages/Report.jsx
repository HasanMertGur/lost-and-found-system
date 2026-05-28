import { useState } from 'react';
import { Camera, MapPin, Tag, AlignLeft, Send } from 'lucide-react';

export default function Report() {
   const [reportType, setReportType] = useState('lost');
   const [itemName, setItemName] = useState('');
   const [categoryId, setCategoryId] = useState('1'); // Tam olarak bu satırın böyle olduğundan emin ol
   const [location, setLocation] = useState('');
   const [description, setDescription] = useState('');
   const [categories, setCategories] = useState([]);
   
   const handleSubmit = (e) => {
      e.preventDefault();
      console.log("1. Butona basıldı, payload hazırlanıyor...");
      
      const payload = {
         user_id: 1, 
         category_id: parseInt(categoryId),
         item_name: itemName,
         description: description,
         type: reportType,
         location: location
      };

      console.log("2. Flask'a gönderilecek veri:", payload);

      fetch('http://127.0.0.1:5000/api/reports', {
         method: 'POST',
         headers: { 'Content-Type': 'application/json' },
         body: JSON.stringify(payload)
      })
      .then(res => {
         console.log("3. Flask sunucusundan yanıt kodu geldi:", res.status);
         return res.json();
      })
      .then(data => {
         console.log("4. Flask'tan gelen ham JSON yanıtı:", data);
         if (data.report_id || data.message === "Ilan olusturuldu.") {
             alert('Harika! İlan başarıyla veritabanına kaydedildi kanka.');
             setItemName('');
             setLocation('');
             setDescription('');
         } else {
             alert('Bir hata oluştu: ' + data.message);
         }
      })
      .catch(err => {
         console.error("🚨 BAĞLANTI HATASI: Flask açık olmayabilir veya CORS engeli var!", err);
         alert("Backend sunucusuna bağlanılamadı. app.py açık mı?");
      });
   };

   return (
      <div className="max-w-2xl mx-auto">
         <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
            <div className="bg-indigo-600 px-6 py-8 text-center text-white">
               <h1 className="text-3xl font-bold mb-2">Report an Item</h1>
               <p className="text-indigo-100">Help the community by reporting what you have lost or found.</p>
            </div>

            <form onSubmit={handleSubmit} className="p-6 sm:p-8 space-y-6">
               {/* Report Type */}
               <div>
                  <label className="block text-sm font-medium text-gray-700 mb-3">What are you reporting?</label>
                  <div className="grid grid-cols-2 gap-4">
                     <button
                        type="button"
                        className={`py-3 px-4 border rounded-xl flex items-center justify-center font-medium transition-colors ${reportType === 'lost' ? 'border-red-500 bg-red-50 text-red-700' : 'border-gray-200 bg-white text-gray-700 hover:bg-gray-50'}`}
                        onClick={() => setReportType('lost')}
                     >
                        I Lost Something
                     </button>
                     <button
                        type="button"
                        className={`py-3 px-4 border rounded-xl flex items-center justify-center font-medium transition-colors ${reportType === 'found' ? 'border-green-500 bg-green-50 text-green-700' : 'border-gray-200 bg-white text-gray-700 hover:bg-gray-50'}`}
                        onClick={() => setReportType('found')}
                     >
                        I Found Something
                     </button>
                  </div>
               </div>

               <hr className="border-gray-100" />

               {/* Item Name */}
               <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Item Title / Name</label>
                  <div className="relative">
                     <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                        <Tag className="h-5 w-5 text-gray-400" />
                     </div>
                     <input type="text" required className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-lg focus:ring-indigo-500 focus:border-indigo-500" placeholder="e.g. Wallet, iPhone 13, Keys" />
                  </div>
               </div>

               <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
                  {/* Category */}
                  <div>
                     <label className="block text-sm font-medium text-gray-700 mb-1">Category</label>
                     <select className="block w-full py-2 px-3 border border-gray-300 bg-white rounded-lg focus:outline-none focus:ring-indigo-500 focus:border-indigo-500">
                        <option value="electronics">Electronics</option>
                        <option value="wallet">Wallet & Bags</option>
                        <option value="keys">Keys</option>
                        <option value="clothing">Clothing</option>
                        <option value="pets">Pets</option>
                        <option value="other">Other</option>
                     </select>
                  </div>

                  {/* Date */}
                  <div>
                     <label className="block text-sm font-medium text-gray-700 mb-1">Date {reportType === 'lost' ? 'Lost' : 'Found'}</label>
                     <input type="date" required className="block w-full py-2 px-3 border border-gray-300 rounded-lg focus:ring-indigo-500 focus:border-indigo-500" />
                  </div>
               </div>

               {/* Location */}
               <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Location</label>
                  <div className="relative">
                     <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                        <MapPin className="h-5 w-5 text-gray-400" />
                     </div>
                     <input type="text" required className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-lg focus:ring-indigo-500 focus:border-indigo-500" placeholder="e.g. Times Square, Central Park" />
                  </div>
               </div>

               {/* Description */}
               <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Detailed Description</label>
                  <div className="relative">
                     <div className="absolute top-2 left-0 pl-3 flex items-start pointer-events-none">
                        <AlignLeft className="h-5 w-5 text-gray-400 mt-1" />
                     </div>
                     <textarea rows={4} required className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-lg focus:ring-indigo-500 focus:border-indigo-500" placeholder="Describe the item, features, colors, brands etc." />
                  </div>
               </div>

               {/* Image */}
               <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Upload Image (Optional)</label>
                  <div className="mt-1 flex justify-center px-6 pt-5 pb-6 border-2 border-gray-300 border-dashed rounded-lg hover:bg-gray-50 transition-colors">
                     <div className="space-y-1 text-center flex flex-col items-center">
                        <Camera className="mx-auto h-12 w-12 text-gray-400" />
                        <div className="flex text-sm text-gray-600 cursor-pointer">
                           <label htmlFor="file-upload" className="relative cursor-pointer bg-white rounded-md font-medium text-indigo-600 hover:text-indigo-500 focus-within:outline-none focus-within:ring-2 focus-within:ring-offset-2 focus-within:ring-indigo-500">
                              <span>Upload a file</span>
                              <input id="file-upload" name="file-upload" type="file" className="sr-only" />
                           </label>
                           <p className="pl-1">or drag and drop</p>
                        </div>
                        <p className="text-xs text-gray-500">PNG, JPG, GIF up to 5MB</p>
                     </div>
                  </div>
               </div>

               <div className="pt-4">
                  <button type="submit" className="w-full flex justify-center items-center py-3 px-4 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 transition-colors">
                     <Send className="mr-2 h-5 w-5" />
                     Submit Report
                  </button>
               </div>
            </form>
         </div>
      </div>
   );
}
