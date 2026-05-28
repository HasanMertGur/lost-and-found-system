import { Outlet, Link } from 'react-router-dom';
import { Search, PlusCircle, UserCircle } from 'lucide-react';

export default function Layout() {
   return (
      <div className="min-h-screen bg-gray-50 flex flex-col">
         <nav className="bg-white shadow">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
               <div className="flex justify-between h-16">
                  <div className="flex">
                     <Link to="/" className="flex-shrink-0 flex items-center">
                        <span className="text-2xl font-bold text-indigo-600">Lost&Found</span>
                     </Link>
                  </div>
                  <div className="flex items-center space-x-4">
                     <Link to="/" className="text-gray-600 hover:text-indigo-600 flex items-center px-3 py-2 rounded-md text-sm font-medium">
                        <Search className="h-5 w-5 mr-1" /> Browse
                     </Link>
                     <Link to="/report" className="bg-indigo-600 text-white hover:bg-indigo-700 flex items-center px-4 py-2 rounded-md text-sm font-medium transition-colors">
                        <PlusCircle className="h-5 w-5 mr-1" /> Report Item
                     </Link>
                     <div className="ml-4 flex items-center">
                        <button className="bg-gray-100 p-2 rounded-full text-gray-500 hover:text-indigo-600 focus:outline-none">
                           <UserCircle className="h-6 w-6" />
                        </button>
                     </div>
                  </div>
               </div>
            </div>
         </nav>

         <main className="flex-grow max-w-7xl w-full mx-auto py-6 sm:px-6 lg:px-8">
            <Outlet />
         </main>

         <footer className="bg-white border-t border-gray-200 mt-auto">
            <div className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
               <p className="text-center text-sm text-gray-500">
                  &copy; {new Date().getFullYear()} Lost & Found System. All rights reserved.
               </p>
            </div>
         </footer>
      </div>
   );
}
