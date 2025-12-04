import React, { Component } from "react";
import ThanhLienKet from "../../../components/ThanhLienKet";
import "./index.css";

class HuongDan extends Component {
  componentDidMount() {
    document.title = "Dich vụ công | Thành viên nhóm";
  }
  render() {
    return (
      <div className="mt-5 pt-5">
        <ThanhLienKet
          key="1"
          text1="Trang chủ"
          link1="/"
          text2="Thành viên nhóm"
          link2="/thanhvien"
        />
        <section className="team-section py-5">
          <div className="container">
            <div className="row justify-content-center">
              {/*//col*/}
              <div className="col-12 col-md-6 col-lg-4">
                <div className="card border-0 shadow-lg pt-5 my-5 position-relative">
                  <div className="card-body p-4">
                    <div className="member-profile position-absolute w-100 text-center">
                      <img
                        className="rounded-circle mx-auto d-inline-block shadow-sm"
                        src="https://bootdey.com/img/Content/avatar/avatar8.png"
                        alt
                      />
                    </div>
                    <div className="card-text pt-1">
                      <h5 className="member-name mb-0 text-center text-primary font-weight-bold">
                        Nguyễn Gia Hiếu
                      </h5>
                      <div className="mb-3 text-center">19520543</div>
                      <div>
                      Backend: Model câu hỏi, đăng nhập, đăng kí, ...
                      </div>
                    </div>
                  </div>
                  {/*//card-body*/}
                  <div className="card-footer theme-bg-primary border-0 text-center">
                    <ul className="social-list list-inline mb-0 mx-auto">
                      <li className="list-inline-item">
                        
                      </li>
                      <li className="list-inline-item">
                        <a className="text-dark" href="https://www.facebook.com/GiaHieu.01">
                          <svg
                            className="svg-inline--fa fa-facebook-f fa-w-10 fa-fw"
                            aria-hidden="true"
                            focusable="false"
                            data-prefix="fab"
                            data-icon="facebook-f"
                            role="img"
                            xmlns="http://www.w3.org/2000/svg"
                            viewBox="0 0 320 512"
                            data-fa-i2svg
                          >
                            <path
                              fill="currentColor"
                              d="M279.14 288l14.22-92.66h-88.91v-60.13c0-25.35 12.42-50.06 52.24-50.06h40.42V6.26S260.43 0 225.36 0c-73.22 0-121.08 44.38-121.08 124.72v70.62H22.89V288h81.39v224h100.17V288z"
                            />
                          </svg>
                          {/* <i class="fab fa-facebook-f fa-fw"></i> Font Awesome fontawesome.com */}
                        </a>
                      </li>
                      <li className="list-inline-item">
                        
                      </li>
                    </ul>
                    {/*//social-list*/}
                  </div>
                  {/*//card-footer*/}
                </div>
                {/*//card*/}
              </div>
              {/*//col*/}
              <div className="col-12 col-md-6 col-lg-4">
                <div className="card border-0 shadow-lg pt-5 my-5 position-relative">
                  <div className="card-body p-4">
                    <div className="member-profile position-absolute w-100 text-center">
                      <img
                        className="rounded-circle mx-auto d-inline-block shadow-sm"
                        src="https://bootdey.com/img/Content/avatar/avatar2.png"
                        alt
                      />
                    </div>
                    <div className="card-text pt-1">
                      <h5 className="member-name mb-0 text-center text-primary font-weight-bold">
                        Phạm Ngọc Thành
                      </h5>
                      <div className="mb-3 text-center">19520958</div>
                      <div>
                      Backend:Model user, Upload file, Download file, Oauth, Kí file; HTTPS, Cloud...
                      </div>
                    </div>
                  </div>
                  {/*//card-body*/}
                  <div className="card-footer theme-bg-primary border-0 text-center">
                    <ul className="social-list list-inline mb-0 mx-auto">
                      <li className="list-inline-item">
<a className="text-dark" href="https://www.facebook.com/thanhzingnew">
                          <svg
                            className="svg-inline--fa fa-facebook-f fa-w-10 fa-fw"
                            aria-hidden="true"
                            focusable="false"
                            data-prefix="fab"
                            data-icon="facebook-f"
                            role="img"
                            xmlns="http://www.w3.org/2000/svg"
                            viewBox="0 0 320 512"
                            data-fa-i2svg
                          >
                            <path
                              fill="currentColor"
                              d="M279.14 288l14.22-92.66h-88.91v-60.13c0-25.35 12.42-50.06 52.24-50.06h40.42V6.26S260.43 0 225.36 0c-73.22 0-121.08 44.38-121.08 124.72v70.62H22.89V288h81.39v224h100.17V288z"
                            />
                          </svg>
                          {/* <i class="fab fa-facebook-f fa-fw"></i> Font Awesome fontawesome.com */}
                        </a> 
                      
                      </li>
                      <li className="list-inline-item">
                         <a className="text-dark" href="https://github.com/phmngcthanh">
                          <svg
                            className="svg-inline--fa fa-github fa-w-16 fa-fw"
                            aria-hidden="true"
                            focusable="false"
                            data-prefix="fab"
                            data-icon="github"
                            role="img"
                            xmlns="http://www.w3.org/2000/svg"
                            viewBox="0 0 496 512"
                            data-fa-i2svg
                          >
                            <path
                              fill="currentColor"
                              d="M165.9 397.4c0 2-2.3 3.6-5.2 3.6-3.3.3-5.6-1.3-5.6-3.6 0-2 2.3-3.6 5.2-3.6 3-.3 5.6 1.3 5.6 3.6zm-31.1-4.5c-.7 2 1.3 4.3 4.3 4.9 2.6 1 5.6 0 6.2-2s-1.3-4.3-4.3-5.2c-2.6-.7-5.5.3-6.2 2.3zm44.2-1.7c-2.9.7-4.9 2.6-4.6 4.9.3 2 2.9 3.3 5.9 2.6 2.9-.7 4.9-2.6 4.6-4.6-.3-1.9-3-3.2-5.9-2.9zM244.8 8C106.1 8 0 113.3 0 252c0 110.9 69.8 205.8 169.5 239.2 12.8 2.3 17.3-5.6 17.3-12.1 0-6.2-.3-40.4-.3-61.4 0 0-70 15-84.7-29.8 0 0-11.4-29.1-27.8-36.6 0 0-22.9-15.7 1.6-15.4 0 0 24.9 2 38.6 25.8 21.9 38.6 58.6 27.5 72.9 20.9 2.3-16 8.8-27.1 16-33.7-55.9-6.2-112.3-14.3-112.3-110.5 0-27.5 7.6-41.3 23.6-58.9-2.6-6.5-11.1-33.3 2.6-67.9 20.9-6.5 69 27 69 27 20-5.6 41.5-8.5 62.8-8.5s42.8 2.9 62.8 8.5c0 0 48.1-33.6 69-27 13.7 34.7 5.2 61.4 2.6 67.9 16 17.7 25.8 31.5 25.8 58.9 0 96.5-58.9 104.2-114.8 110.5 9.2 7.9 17 22.9 17 46.4 0 33.7-.3 75.4-.3 83.6 0 6.5 4.6 14.4 17.3 12.1C428.2 457.8 496 362.9 496 252 496 113.3 383.5 8 244.8 8zM97.2 352.9c-1.3 1-1 3.3.7 5.2 1.6 1.6 3.9 2.3 5.2 1 1.3-1 1-3.3-.7-5.2-1.6-1.6-3.9-2.3-5.2-1zm-10.8-8.1c-.7 1.3.3 2.9 2.3 3.9 1.6 1 3.6.7 4.3-.7.7-1.3-.3-2.9-2.3-3.9-2-.6-3.6-.3-4.3.7zm32.4 35.6c-1.6 1.3-1 4.3 1.3 6.2 2.3 2.3 5.2 2.6 6.5 1 1.3-1.3.7-4.3-1.3-6.2-2.2-2.3-5.2-2.6-6.5-1zm-11.4-14.7c-1.6 1-1.6 3.6 0 5.9 1.6 2.3 4.3 3.3 5.6 2.3 1.6-1.3 1.6-3.9 0-6.2-1.4-2.3-4-3.3-5.6-2z"
                            />
                          </svg>
                       
                        </a>
                      </li>
                    </ul>
                    {/*//social-list*/}
                  </div>
                  {/*//card-footer*/}
                </div>
                {/*//card*/}
              </div>
              {/*//col*/}
              <div className="col-12 col-md-6 col-lg-4">
                <div className="card border-0 shadow-lg pt-5 my-5 position-relative">
                  <div className="card-body p-4">
                    <div className="member-profile position-absolute w-100 text-center">
                      <img
                        className="rounded-circle mx-auto d-inline-block shadow-sm"
                        src="https://bootdey.com/img/Content/avatar/avatar3.png"
                        alt
                      />
                    </div>
                    <div className="card-text pt-1">
                      <h5 className="member-name mb-0 text-center text-primary font-weight-bold">
                        Trần Anh Khoa
                      </h5>
                      <div className="mb-3 text-center">19520643</div>
                      <div>
                      Frontend: React Developer
                      </div>
                    </div>
                  </div>
                  {/*//card-body*/}
                  <div className="card-footer theme-bg-primary border-0 text-center">
                    <ul className="social-list list-inline mb-0 mx-auto">
                      <li className="list-inline-item">
                       <a className="text-dark" href="https://www.facebook.com/trananh.khoa.7547">
                          <svg
                            className="svg-inline--fa fa-facebook-f fa-w-10 fa-fw"
                            aria-hidden="true"
                            focusable="false"
                            data-prefix="fab"
                            data-icon="facebook-f"
                            role="img"
                            xmlns="http://www.w3.org/2000/svg"
                            viewBox="0 0 320 512"
                            data-fa-i2svg
                          >
                            <path
                              fill="currentColor"
                              d="M279.14 288l14.22-92.66h-88.91v-60.13c0-25.35 12.42-50.06 52.24-50.06h40.42V6.26S260.43 0 225.36 0c-73.22 0-121.08 44.38-121.08 124.72v70.62H22.89V288h81.39v224h100.17V288z"
                            />
                          </svg>
                          {/* <i class="fab fa-facebook-f fa-fw"></i> Font Awesome fontawesome.com */}
                        </a> 
                      
                      </li>
                      <li className="list-inline-item">
                        
                      </li>
                    </ul>
                    {/*//social-list*/}
                  </div>
                  {/*//card-footer*/}
                </div>
                {/*//card*/}
              </div>
              {/*//col*/}
            </div>
            {/*//row*/}
          </div>
        </section>
      </div>
    );
  }
}

export default HuongDan;
